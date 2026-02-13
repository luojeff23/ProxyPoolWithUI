# encoding: utf-8

import os
import io
import csv
import logging
from flask import Flask
from flask import jsonify, request, redirect, send_from_directory, Response

try:
    import config as config_module
    from config import API_HOST, API_PORT
except Exception:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    import config as config_module
    from config import API_HOST, API_PORT

log = logging.getLogger('werkzeug')
log.disabled = True

try:
    from db import conn
except Exception:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from db import conn

STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'frontend', 'deployment')
DEFAULT_RAW_SOURCES_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'sources', 'raw_sources.txt')
ALLOWED_PROTOCOLS = {'http', 'https', 'socks4', 'socks5', 'auto'}

app = Flask(
    __name__,
    static_url_path='/web',
    static_folder=STATIC_FOLDER
)


def _ok(**kwargs):
    return jsonify(dict(success=True, **kwargs))


def _err(message, code=400):
    return jsonify(dict(success=False, message=message)), code


def _safe_int(value, default, min_value=None, max_value=None):
    try:
        n = int(value)
    except Exception:
        n = default
    if min_value is not None and n < min_value:
        n = min_value
    if max_value is not None and n > max_value:
        n = max_value
    return n


def _normalize_validated(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ('all', ''):
        return None
    if text in ('1', 'true', 'yes'):
        return True
    if text in ('0', 'false', 'no'):
        return False
    return None


def _sources_file_path():
    path = os.getenv('RAW_SOURCES_FILE', DEFAULT_RAW_SOURCES_FILE)
    return os.path.abspath(path)


def _validate_source_line(line):
    text = line.strip()
    if text == '' or text.startswith('#'):
        return True, None

    if ',' in text:
        protocol, url = text.split(',', 1)
        protocol = protocol.strip().lower()
        url = url.strip()
        if protocol not in ALLOWED_PROTOCOLS:
            return False, f'协议不合法: {protocol}'
    else:
        url = text

    if not (url.startswith('http://') or url.startswith('https://')):
        return False, f'URL必须以http(s)开头: {url}'
    return True, None


def _runtime_config_snapshot():
    return dict(
        database_path=config_module.DATABASE_PATH,
        api_host=config_module.API_HOST,
        api_port=config_module.API_PORT,
        proc_fetcher_sleep=config_module.PROC_FETCHER_SLEEP,
        proc_validator_sleep=config_module.PROC_VALIDATOR_SLEEP,
        validate_thread_num=config_module.VALIDATE_THREAD_NUM,
        validate_url=config_module.VALIDATE_URL,
        validate_method=config_module.VALIDATE_METHOD,
        validate_header=config_module.VALIDATE_HEADER,
        validate_keyword=config_module.VALIDATE_KEYWORD,
        validate_timeout=config_module.VALIDATE_TIMEOUT,
        validate_max_fails=config_module.VALIDATE_MAX_FAILS,
        raw_sources_file=_sources_file_path(),
        raw_sources_timeout=_safe_int(os.getenv('RAW_SOURCES_TIMEOUT', '8'), 8, 1, 120)
    )


############# 以下API可用于获取代理 ################

# 可用于测试API状态
@app.route('/ping', methods=['GET'])
def ping():
    return 'API OK'


# 随机获取一个可用代理，如果没有可用代理则返回空白
@app.route('/fetch_random', methods=['GET'])
def fetch_random():
    proxies = conn.getValidatedRandom(1)
    if len(proxies) > 0:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    return ''


# api 获取协议为http的一条结果
@app.route('/fetch_http', methods=['GET'])
def fetch_http():
    proxies = conn.get_by_protocol('http', 1)
    if len(proxies) > 0:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    return ''


# api 获取协议为http的全部结果
@app.route('/fetch_http_all', methods=['GET'])
def fetch_http_all():
    proxies = conn.get_by_protocol('http', -1)
    if len(proxies) == 1:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    if len(proxies) > 1:
        proxy_list = []
        for p in proxies:
            proxy_list.append(f'{p.protocol}://{p.ip}:{p.port}')
        return ','.join(proxy_list)
    return ''


# api 获取协议为https的一条结果
@app.route('/fetch_https', methods=['GET'])
def fetch_https():
    proxies = conn.get_by_protocol('https', 1)
    if len(proxies) > 0:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    return ''


# api 获取协议为https的全部结果
@app.route('/fetch_https_all', methods=['GET'])
def fetch_https_all():
    proxies = conn.get_by_protocol('https', -1)
    if len(proxies) == 1:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    if len(proxies) > 1:
        proxy_list = []
        for p in proxies:
            proxy_list.append(f'{p.protocol}://{p.ip}:{p.port}')
        return ','.join(proxy_list)
    return ''


# api 获取协议为socks4的一条结果
@app.route('/fetch_socks4', methods=['GET'])
def fetch_socks4():
    proxies = conn.get_by_protocol('socks4', 1)
    if len(proxies) > 0:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    return ''


# api 获取协议为socks4的全部结果
@app.route('/fetch_socks4_all', methods=['GET'])
def fetch_socks4_all():
    proxies = conn.get_by_protocol('socks4', -1)
    if len(proxies) == 1:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    if len(proxies) > 1:
        proxy_list = []
        for p in proxies:
            proxy_list.append(f'{p.protocol}://{p.ip}:{p.port}')
        return ','.join(proxy_list)
    return ''


# api 获取协议为socks5的一条结果
@app.route('/fetch_socks5', methods=['GET'])
def fetch_socks5():
    proxies = conn.get_by_protocol('socks5', 1)
    if len(proxies) > 0:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    return ''


# api 获取协议为socks5的全部结果
@app.route('/fetch_socks5_all', methods=['GET'])
def fetch_socks5_all():
    proxies = conn.get_by_protocol('socks5', -1)
    if len(proxies) == 1:
        p = proxies[0]
        return f'{p.protocol}://{p.ip}:{p.port}'
    if len(proxies) > 1:
        proxy_list = []
        for p in proxies:
            proxy_list.append(f'{p.protocol}://{p.ip}:{p.port}')
        return ','.join(proxy_list)
    return ''


# 获取所有可用代理，如果没有可用代理则返回空白
@app.route('/fetch_all', methods=['GET'])
def fetch_all():
    proxies = conn.getValidatedRandom(-1)
    proxies = [f'{p.protocol}://{p.ip}:{p.port}' for p in proxies]
    return ','.join(proxies)


############# 以下API主要给网页使用 ################

@app.route('/')
def index():
    return redirect('/web')


def _send_web_page(page):
    return send_from_directory(STATIC_FOLDER, page)


@app.route('/web', methods=['GET'])
@app.route('/web/', methods=['GET'])
def page_index():
    return _send_web_page('index.html')


@app.route('/web/fetchers', methods=['GET'])
@app.route('/web/fetchers/', methods=['GET'])
def page_fetchers():
    return _send_web_page('fetchers/index.html')


@app.route('/web/dashboard', methods=['GET'])
@app.route('/web/dashboard/', methods=['GET'])
def page_dashboard():
    return _send_web_page('dashboard/index.html')


@app.route('/web/proxies', methods=['GET'])
@app.route('/web/proxies/', methods=['GET'])
def page_proxies():
    return _send_web_page('proxies/index.html')


@app.route('/web/sources', methods=['GET'])
@app.route('/web/sources/', methods=['GET'])
def page_sources():
    return _send_web_page('sources/index.html')


@app.route('/web/system', methods=['GET'])
@app.route('/web/system/', methods=['GET'])
def page_system():
    return _send_web_page('system/index.html')


# 获取代理状态
@app.route('/proxies_status', methods=['GET'])
def proxies_status():
    proxies = conn.getValidatedRandom(-1)
    proxies = sorted(proxies, key=lambda p: f'{p.protocol}://{p.ip}:{p.port}', reverse=True)
    proxies = [p.to_dict() for p in proxies]

    status = conn.getProxiesStatus()

    return _ok(
        proxies=proxies,
        **status
    )


# 获取爬取器状态
@app.route('/fetchers_status', methods=['GET'])
def fetchers_status():
    proxies = conn.getValidatedRandom(-1)  # 获取所有可用代理
    fetchers = conn.getAllFetchers()
    fetchers = [f.to_dict() for f in fetchers]

    for f in fetchers:
        f['validated_cnt'] = len([_ for _ in proxies if _.fetcher_name == f['name']])
        f['in_db_cnt'] = conn.getProxyCount(f['name'])

    return _ok(fetchers=fetchers)


# 清空爬取器状态
@app.route('/clear_fetchers_status', methods=['GET'])
def clear_fetchers_status():
    conn.pushClearFetchersStatus()
    return _ok()


# 设置是否启用特定爬取器,?name=str,enable=0/1
@app.route('/fetcher_enable', methods=['GET'])
def fetcher_enable():
    name = request.args.get('name')
    enable = request.args.get('enable')
    if enable == '1':
        conn.pushFetcherEnable(name, True)
    else:
        conn.pushFetcherEnable(name, False)
    return _ok()


############# 管理后台API ################

@app.route('/admin/proxies', methods=['GET'])
def admin_proxies():
    protocol = request.args.get('protocol')
    fetcher_name = request.args.get('fetcher_name')
    validated = _normalize_validated(request.args.get('validated'))
    keyword = request.args.get('keyword', '')
    page = _safe_int(request.args.get('page', 1), 1, 1)
    page_size = _safe_int(request.args.get('page_size', 50), 50, 1, 500)

    total = conn.countProxies(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword
    )
    proxies = conn.queryProxies(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword,
        page=page,
        page_size=page_size
    )

    return _ok(
        items=[p.to_dict() for p in proxies],
        total=total,
        page=page,
        page_size=page_size
    )


@app.route('/admin/proxies/export.csv', methods=['GET'])
def admin_proxies_export_csv():
    protocol = request.args.get('protocol')
    fetcher_name = request.args.get('fetcher_name')
    validated = _normalize_validated(request.args.get('validated'))
    keyword = request.args.get('keyword', '')

    total = conn.countProxies(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword
    )
    page_size = max(1, min(total if total > 0 else 1, 50000))
    proxies = conn.queryProxies(
        protocol=protocol,
        fetcher_name=fetcher_name,
        validated=validated,
        keyword=keyword,
        page=1,
        page_size=page_size
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'protocol', 'ip', 'port', 'fetcher_name',
        'validated', 'latency', 'validate_date',
        'to_validate_date', 'validate_failed_cnt'
    ])
    for p in proxies:
        item = p.to_dict()
        writer.writerow([
            item['protocol'], item['ip'], item['port'], item['fetcher_name'],
            item['validated'], item['latency'], item['validate_date'],
            item['to_validate_date'], item['validate_failed_cnt']
        ])

    csv_text = output.getvalue()
    output.close()

    return Response(
        csv_text,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=proxies.csv'}
    )


@app.route('/admin/sources', methods=['GET'])
def admin_sources_get():
    path = _sources_file_path()
    if not os.path.exists(path):
        return _ok(file_path=path, lines=[])

    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
    return _ok(file_path=path, lines=lines)


@app.route('/admin/sources', methods=['PUT'])
def admin_sources_put():
    body = request.get_json(silent=True) or {}
    lines = body.get('lines')
    if not isinstance(lines, list):
        return _err('lines必须是字符串数组')

    invalid_lines = []
    for i, line in enumerate(lines, start=1):
        if not isinstance(line, str):
            invalid_lines.append(dict(line_no=i, line=str(line), message='必须是字符串'))
            continue
        ok, msg = _validate_source_line(line)
        if not ok:
            invalid_lines.append(dict(line_no=i, line=line, message=msg))

    if len(invalid_lines) > 0:
        return jsonify(dict(success=False, message='存在不合法的源配置行', invalid_lines=invalid_lines)), 400

    path = _sources_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines).rstrip('\n') + '\n')

    valid_count = 0
    for line in lines:
        text = line.strip()
        if text != '' and not text.startswith('#'):
            valid_count += 1

    return _ok(
        file_path=path,
        valid_count=valid_count,
        invalid_lines=[]
    )


@app.route('/admin/health', methods=['GET'])
def admin_health():
    db_ok = True
    db_error = None
    try:
        conn.getProxiesStatus()
    except Exception as err:
        db_ok = False
        db_error = str(err)

    fetchers = conn.getAllFetchers() if db_ok else []
    enabled_fetchers = [f.name for f in fetchers if f.enable]
    recent_errors = conn.getRecentFetcherErrors(20) if db_ok else []

    return _ok(
        api_ok=True,
        db_ok=db_ok,
        db_error=db_error,
        fetchers_registered=len(fetchers),
        enabled_fetchers=enabled_fetchers,
        recent_errors=recent_errors
    )


@app.route('/admin/summary', methods=['GET'])
def admin_summary():
    status = conn.getProxiesStatus()
    fetchers = [f.to_dict() for f in conn.getAllFetchers()]
    fetcher_proxy_stats = conn.getFetcherProxyStats()
    protocol_stats = conn.getProtocolStats()
    recent_errors = conn.getRecentFetcherErrors(20)

    for fetcher in fetchers:
        stats = fetcher_proxy_stats.get(fetcher['name'], dict(in_db_cnt=0, validated_cnt=0))
        fetcher['in_db_cnt'] = stats['in_db_cnt']
        fetcher['validated_cnt'] = stats['validated_cnt']

    return _ok(
        status=status,
        protocol_stats=protocol_stats,
        fetchers=fetchers,
        recent_errors=recent_errors,
        runtime_config=_runtime_config_snapshot()
    )


@app.route('/admin/maintenance/clear_fetchers_stats', methods=['POST'])
def admin_clear_fetchers_stats():
    body = request.get_json(silent=True) or {}
    confirm_text = str(body.get('confirm_text', '')).strip()
    if confirm_text != 'CLEAR_FETCHERS_STATS':
        return _err('确认词错误，需要输入 CLEAR_FETCHERS_STATS', 400)
    conn.pushClearFetchersStatus()
    return _ok()


@app.route('/admin/maintenance/clear_proxies', methods=['POST'])
def admin_clear_proxies():
    body = request.get_json(silent=True) or {}
    confirm_text = str(body.get('confirm_text', '')).strip()
    if confirm_text != 'CLEAR_PROXIES':
        return _err('确认词错误，需要输入 CLEAR_PROXIES', 400)
    conn.clearProxies()
    return _ok()


############# 其他 ################

# 跨域支持，主要是在开发网页端的时候需要使用
def after_request(resp):
    allowed_origin = ['0.0.0.0', '127.0.0.1', 'localhost']
    origin = request.headers.get('origin', None)
    if origin is not None:
        for item in allowed_origin:
            if item in origin:
                resp.headers['Access-Control-Allow-Origin'] = origin
                resp.headers['Access-Control-Allow-Credentials'] = 'true'
    return resp


app.after_request(after_request)


def main(proc_lock):
    if proc_lock is not None:
        conn.set_proc_lock(proc_lock)
    # 因为默认sqlite3中，同一个数据库连接不能在多线程环境下使用，所以这里需要禁用flask的多线程
    app.run(host=API_HOST, port=API_PORT, threaded=False)


if __name__ == '__main__':
    main(None)
