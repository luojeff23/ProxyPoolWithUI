# encoding: utf-8
"""
定时运行爬取器
"""

import sys
import threading
from queue import Queue
import logging
import time
from db import conn
from fetchers import fetchers
from config import PROC_FETCHER_SLEEP

try:
    from func_timeout import func_set_timeout
    from func_timeout.exceptions import FunctionTimedOut
except ImportError:
    # 在缺少func-timeout依赖时退化为普通调用，避免启动失败
    def func_set_timeout(_timeout_seconds):
        def decorator(func):
            return func
        return decorator

    class FunctionTimedOut(TimeoutError):
        pass

logging.basicConfig(stream=sys.stdout, format="%(asctime)s-%(levelname)s:%(name)s:%(message)s", level='INFO')

def main(proc_lock):
    """
    定时运行爬取器
    主要逻辑：
    While True:
        for 爬取器 in 所有爬取器:
            查询数据库，判断当前爬取器是否需要运行
            如果需要运行，那么启动线程运行该爬取器
        等待所有线程结束
        将爬取到的代理放入数据库中
        睡眠一段时间
    """
    logger = logging.getLogger('fetcher')
    conn.set_proc_lock(proc_lock)

    while True:
        logger.info('开始运行一轮爬取器')
        status = conn.getProxiesStatus()
        if status['pending_proxies_cnt'] > 2000:
            logger.info(f"还有{status['pending_proxies_cnt']}个代理等待验证，数量过多，跳过本次爬取")
            time.sleep(PROC_FETCHER_SLEEP)
            continue

        @func_set_timeout(30)
        def fetch_worker(fetcher):
            f = fetcher()
            proxies = f.fetch()
            return proxies

        def run_thread(name, fetcher, que):
            """
            name: 爬取器名称
            fetcher: 爬取器class
            que: 队列，用于返回数据
            """
            try:
                proxies = fetch_worker(fetcher)
                que.put((name, proxies))
            except FunctionTimedOut:
                conn.pushFetcherError(name, 'fetch worker timeout')
                que.put((name, []))
            except Exception as e:
                logger.error(f'运行爬取器{name}出错：' + str(e))
                conn.pushFetcherError(name, str(e))
                que.put((name, []))

        threads = []
        enabled_fetchers = []
        que = Queue()
        for item in fetchers:
            data = conn.getFetcher(item.name)
            if data is None:
                logger.error(f'没有在数据库中找到对应的信息：{item.name}')
                raise ValueError('不可恢复错误')
            if not data.enable:
                logger.info(f'跳过爬取器{item.name}')
                continue
            enabled_fetchers.append(item.name)
            threads.append(
                threading.Thread(
                    target=run_thread,
                    args=(item.name, item.fetcher, que),
                    name=f'fetcher:{item.name}',
                    daemon=True
                )
            )
        [t.start() for t in threads]
        round_deadline = time.time() + 35
        for t in threads:
            remaining = round_deadline - time.time()
            if remaining > 0:
                t.join(timeout=remaining)
            if t.is_alive():
                logger.error(f'爬取线程执行超时：{t.name}')
                conn.pushFetcherError(t.name.replace('fetcher:', ''), 'thread join timeout')

        fetcher_results = {name: 0 for name in enabled_fetchers}
        while not que.empty():
            fetcher_name, proxies = que.get()
            fetcher_results[fetcher_name] = len(proxies)
            for proxy in proxies:
                conn.pushNewFetch(fetcher_name, proxy[0], proxy[1], proxy[2])
        for fetcher_name, proxies_cnt in fetcher_results.items():
            conn.pushFetcherResult(fetcher_name, proxies_cnt)
        
        logger.info(f'完成运行{len(threads)}个爬取器，睡眠{PROC_FETCHER_SLEEP}秒')
        time.sleep(PROC_FETCHER_SLEEP)
