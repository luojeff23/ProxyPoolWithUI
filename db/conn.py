# encoding: utf-8

"""
封装的数据库接口
"""

from config import DATABASE_PATH
from .Proxy import Proxy
from .Fetcher import Fetcher
import sqlite3
import datetime
import threading

conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
# 线程锁
conn_lock = threading.Lock()
# 进程锁
proc_lock = None


def _acquire_locks():
    conn_lock.acquire()
    if proc_lock is not None:
        proc_lock.acquire()


def _release_locks():
    if proc_lock is not None:
        try:
            proc_lock.release()
        except ValueError:
            pass
    conn_lock.release()


def set_proc_lock(proc_lock_sub):
    """
    设置进程锁
    proc_lock_sub : main中的进程锁
    """
    global proc_lock
    proc_lock = proc_lock_sub


def pushNewFetch(fetcher_name, protocol, ip, port):
    """
    爬取器新抓到了一个代理，调用本函数将代理放入数据库
    fetcher_name : 爬取器名称
    protocol : 代理协议
    ip : 代理IP地址
    port : 代理端口
    """
    p = Proxy()
    p.fetcher_name = fetcher_name
    p.protocol = protocol
    p.ip = ip
    p.port = port

    _acquire_locks()
    try:
        c = conn.cursor()
        c.execute('BEGIN EXCLUSIVE TRANSACTION;')
        # 更新proxies表
        c.execute('SELECT * FROM proxies WHERE protocol=? AND ip=? AND port=?', (p.protocol, p.ip, p.port))
        row = c.fetchone()
        if row is not None:  # 已经存在(protocol, ip, port)
            old_p = Proxy.decode(row)
            c.execute("""
                UPDATE proxies SET fetcher_name=?,to_validate_date=? WHERE protocol=? AND ip=? AND port=?
            """, (p.fetcher_name, min(datetime.datetime.now(), old_p.to_validate_date), p.protocol, p.ip, p.port))
        else:
            c.execute('INSERT INTO proxies VALUES (?,?,?,?,?,?,?,?,?)', p.params())
        c.close()
        conn.commit()
    finally:
        _release_locks()


def getToValidate(max_count=1):
    """
    从数据库中获取待验证的代理，根据to_validate_date字段
    优先选取已经通过了验证的代理，其次是没有通过验证的代理
    max_count : 返回数量限制
    返回 : list[Proxy]
    """
    _acquire_locks()
    try:
        c = conn.cursor()
        c.execute('BEGIN EXCLUSIVE TRANSACTION;')
        c.execute('SELECT * FROM proxies WHERE to_validate_date<=? AND validated=? ORDER BY to_validate_date LIMIT ?', (
            datetime.datetime.now(),
            True,
            max_count
        ))
        proxies = [Proxy.decode(row) for row in c]
        c.execute('SELECT * FROM proxies WHERE to_validate_date<=? AND validated=? ORDER BY to_validate_date LIMIT ?', (
            datetime.datetime.now(),
            False,
            max_count - len(proxies)
        ))
        proxies = proxies + [Proxy.decode(row) for row in c]
        c.close()
        conn.commit()
        return proxies
    finally:
        _release_locks()


def pushValidateResult(proxy, success, latency):
    """
    将验证器的一个结果添加进数据库中
    proxy : 代理
    success : True/False，验证是否成功
    latency : 本次验证所用的时间(单位毫秒)
    """
    p = proxy
    should_remove = p.validate(success, latency)
    _acquire_locks()
    try:
        if should_remove:
            conn.execute('DELETE FROM proxies WHERE protocol=? AND ip=? AND port=?', (p.protocol, p.ip, p.port))
        else:
            conn.execute("""
                UPDATE proxies
                SET fetcher_name=?,validated=?,latency=?,validate_date=?,to_validate_date=?,validate_failed_cnt=?
                WHERE protocol=? AND ip=? AND port=?
            """, (
                p.fetcher_name, p.validated, p.latency, p.validate_date, p.to_validate_date, p.validate_failed_cnt,
                p.protocol, p.ip, p.port
            ))
        conn.commit()
    finally:
        _release_locks()


def getValidatedRandom(max_count):
    """
    从通过了验证的代理中，随机选择max_count个代理返回
    max_count<=0表示不做数量限制
    返回 : list[Proxy]
    """
    _acquire_locks()
    try:
        if max_count > 0:
            r = conn.execute('SELECT * FROM proxies WHERE validated=? ORDER BY RANDOM() LIMIT ?', (True, max_count))
        else:
            r = conn.execute('SELECT * FROM proxies WHERE validated=? ORDER BY RANDOM()', (True,))
        proxies = [Proxy.decode(row) for row in r]
        r.close()
        return proxies
    finally:
        _release_locks()


def get_by_protocol(protocol, max_count):
    """
    查询 protocol 字段为指定值的代理服务器记录
    max_count 表示返回记录的最大数量，如果为 0 或负数则返回所有记录
    返回 : list[Proxy]
    """
    _acquire_locks()
    try:
        if max_count > 0:
            r = conn.execute('SELECT * FROM proxies WHERE protocol=? AND validated=? ORDER BY RANDOM() LIMIT ?', (protocol, True, max_count))
        else:
            r = conn.execute('SELECT * FROM proxies WHERE protocol=? AND validated=? ORDER BY RANDOM()', (protocol, True))
        proxies = [Proxy.decode(row) for row in r]
        r.close()
        return proxies
    finally:
        _release_locks()


def pushFetcherResult(name, proxies_cnt):
    """
    更新爬取器的状态，每次在完成一个网站的爬取之后，调用本函数
    name : 爬取器的名称
    proxies_cnt : 本次爬取到的代理数量
    """
    _acquire_locks()
    try:
        c = conn.cursor()
        c.execute('BEGIN EXCLUSIVE TRANSACTION;')
        c.execute('SELECT * FROM fetchers WHERE name=?', (name,))
        row = c.fetchone()
        if row is None:
            raise ValueError(f'ERRROR: can not find fetcher {name}')
        else:
            f = Fetcher.decode(row)
            f.last_proxies_cnt = proxies_cnt
            f.sum_proxies_cnt = f.sum_proxies_cnt + proxies_cnt
            f.last_fetch_date = datetime.datetime.now()
            c.execute('UPDATE fetchers SET sum_proxies_cnt=?,last_proxies_cnt=?,last_fetch_date=? WHERE name=?', (
                f.sum_proxies_cnt, f.last_proxies_cnt, f.last_fetch_date, f.name
            ))
        c.close()
        conn.commit()
    finally:
        _release_locks()


def pushFetcherEnable(name, enable):
    """
    设置是否起用对应爬取器，被禁用的爬取器将不会被运行
    name : 爬取器的名称
    enable : True/False, 是否启用
    """
    _acquire_locks()
    try:
        c = conn.cursor()
        c.execute('BEGIN EXCLUSIVE TRANSACTION;')
        c.execute('SELECT * FROM fetchers WHERE name=?', (name,))
        row = c.fetchone()
        if row is None:
            raise ValueError(f'ERRROR: can not find fetcher {name}')
        else:
            f = Fetcher.decode(row)
            f.enable = enable
            c.execute('UPDATE fetchers SET enable=? WHERE name=?', (
                f.enable, f.name
            ))
        c.close()
        conn.commit()
    finally:
        _release_locks()


def getAllFetchers():
    """
    获取所有的爬取器以及状态
    返回 : list[Fetcher]
    """
    _acquire_locks()
    try:
        r = conn.execute('SELECT * FROM fetchers')
        fetchers = [Fetcher.decode(row) for row in r]
        r.close()
        return fetchers
    finally:
        _release_locks()


def getFetcher(name):
    """
    获取指定爬取器以及状态
    返回 : Fetcher
    """
    _acquire_locks()
    try:
        r = conn.execute('SELECT * FROM fetchers WHERE name=?', (name,))
        row = r.fetchone()
        r.close()
    finally:
        _release_locks()

    if row is None:
        return None
    return Fetcher.decode(row)


def getProxyCount(fetcher_name):
    """
    查询在数据库中有多少个由指定爬取器爬取到的代理
    fetcher_name : 爬取器名称
    返回 : int
    """
    _acquire_locks()
    try:
        r = conn.execute('SELECT count(*) FROM proxies WHERE fetcher_name=?', (fetcher_name,))
        cnt = r.fetchone()[0]
        r.close()
        return cnt
    finally:
        _release_locks()


def getProxiesStatus():
    """
    获取代理状态，包括`全部代理数量`，`当前可用代理数量`，`等待验证代理数量`
    返回 : dict
    """
    _acquire_locks()
    try:
        r = conn.execute('SELECT count(*) FROM proxies')
        sum_proxies_cnt = r.fetchone()[0]
        r.close()

        r = conn.execute('SELECT count(*) FROM proxies WHERE validated=?', (True,))
        validated_proxies_cnt = r.fetchone()[0]
        r.close()

        r = conn.execute('SELECT count(*) FROM proxies WHERE to_validate_date<=?', (datetime.datetime.now(),))
        pending_proxies_cnt = r.fetchone()[0]
        r.close()

        return dict(
            sum_proxies_cnt=sum_proxies_cnt,
            validated_proxies_cnt=validated_proxies_cnt,
            pending_proxies_cnt=pending_proxies_cnt
        )
    finally:
        _release_locks()


def pushClearFetchersStatus():
    """
    清空爬取器的统计信息，包括sum_proxies_cnt,last_proxies_cnt,last_fetch_date
    """
    _acquire_locks()
    try:
        c = conn.cursor()
        c.execute('BEGIN EXCLUSIVE TRANSACTION;')
        c.execute('UPDATE fetchers SET sum_proxies_cnt=?, last_proxies_cnt=?, last_fetch_date=?', (0, 0, None))
        c.close()
        conn.commit()
    finally:
        _release_locks()


def clearProxies():
    """
    清空代理池中的所有代理记录
    """
    _acquire_locks()
    try:
        conn.execute('DELETE FROM proxies')
        conn.commit()
    finally:
        _release_locks()


def _build_proxy_query_filters(protocol=None, fetcher_name=None, validated=None, keyword=None):
    where_clauses = []
    params = []

    if protocol is not None and protocol != '' and protocol != 'all':
        where_clauses.append('protocol=?')
        params.append(protocol)

    if fetcher_name is not None and fetcher_name != '' and fetcher_name != 'all':
        where_clauses.append('fetcher_name=?')
        params.append(fetcher_name)

    if validated is not None and validated != 'all':
        if isinstance(validated, str):
            val = validated.strip().lower()
            if val in ('1', 'true', 'yes'):
                validated = True
            elif val in ('0', 'false', 'no'):
                validated = False
            else:
                validated = None
        if validated is not None:
            where_clauses.append('validated=?')
            params.append(bool(validated))

    if keyword is not None and keyword.strip() != '':
        kw = '%' + keyword.strip() + '%'
        where_clauses.append('(ip LIKE ? OR CAST(port AS TEXT) LIKE ? OR fetcher_name LIKE ?)')
        params.extend([kw, kw, kw])

    if len(where_clauses) == 0:
        return '', params
    return ' WHERE ' + ' AND '.join(where_clauses), params


def queryProxies(protocol=None, fetcher_name=None, validated=None, keyword=None, page=1, page_size=50):
    """
    分页查询代理列表
    """
    page = max(int(page), 1)
    page_size = max(int(page_size), 1)
    offset = (page - 1) * page_size

    where_sql, params = _build_proxy_query_filters(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword
    )

    sql = (
        'SELECT * FROM proxies'
        + where_sql
        + ' ORDER BY validated DESC, latency ASC, to_validate_date ASC LIMIT ? OFFSET ?'
    )
    params = params + [page_size, offset]

    _acquire_locks()
    try:
        r = conn.execute(sql, tuple(params))
        proxies = [Proxy.decode(row) for row in r]
        r.close()
        return proxies
    finally:
        _release_locks()


def countProxies(protocol=None, fetcher_name=None, validated=None, keyword=None):
    """
    查询符合条件的代理总数
    """
    where_sql, params = _build_proxy_query_filters(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword
    )
    sql = 'SELECT count(*) FROM proxies' + where_sql

    _acquire_locks()
    try:
        r = conn.execute(sql, tuple(params))
        cnt = int(r.fetchone()[0])
        r.close()
        return cnt
    finally:
        _release_locks()


def getProtocolStats():
    """
    返回按协议聚合的统计
    """
    _acquire_locks()
    try:
        totals = {}
        validated = {}

        r = conn.execute('SELECT protocol, count(*) FROM proxies GROUP BY protocol')
        for row in r:
            totals[row[0]] = int(row[1])
        r.close()

        r = conn.execute('SELECT protocol, count(*) FROM proxies WHERE validated=? GROUP BY protocol', (True,))
        for row in r:
            validated[row[0]] = int(row[1])
        r.close()

        protocols = sorted(set(list(totals.keys()) + list(validated.keys())))
        stats = []
        for protocol in protocols:
            stats.append(dict(
                protocol=protocol,
                total=totals.get(protocol, 0),
                validated=validated.get(protocol, 0)
            ))
        return stats
    finally:
        _release_locks()


def getFetcherProxyStats():
    """
    返回每个爬取器在proxies表中的统计(总量+可用量)
    """
    _acquire_locks()
    try:
        r = conn.execute("""
            SELECT fetcher_name, count(*) as in_db_cnt,
                   sum(CASE WHEN validated=1 THEN 1 ELSE 0 END) as validated_cnt
            FROM proxies
            GROUP BY fetcher_name
        """)
        result = {}
        for row in r:
            result[row[0]] = dict(
                in_db_cnt=int(row[1]),
                validated_cnt=int(row[2]) if row[2] is not None else 0
            )
        r.close()
        return result
    finally:
        _release_locks()


def pushFetcherError(fetcher_name, error_message):
    """
    记录抓取器错误日志
    """
    _acquire_locks()
    try:
        conn.execute(
            'INSERT INTO fetcher_errors(fetcher_name,error_message,created_at) VALUES (?,?,?)',
            (fetcher_name, str(error_message), datetime.datetime.now())
        )
        conn.commit()
    finally:
        _release_locks()


def getRecentFetcherErrors(limit=20):
    """
    获取最近的抓取器错误日志
    """
    limit = max(int(limit), 1)
    _acquire_locks()
    try:
        r = conn.execute(
            'SELECT id,fetcher_name,error_message,created_at FROM fetcher_errors ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        items = []
        for row in r:
            items.append(dict(
                id=int(row[0]),
                fetcher_name=row[1],
                error_message=row[2],
                created_at=str(row[3]) if row[3] is not None else None
            ))
        r.close()
        return items
    finally:
        _release_locks()
