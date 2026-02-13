# encoding: utf-8

from collections import namedtuple
import importlib
import logging

Fetcher = namedtuple('Fetcher', ['name', 'fetcher'])

_logger = logging.getLogger(__name__)

_FETCHER_SPECS = [
    ('raw-sources', 'RawSourcesFetcher', 'RawSourcesFetcher'),
    ('uu-proxy.com', 'UUFetcher', 'UUFetcher'),
    ('www.kuaidaili.com', 'KuaidailiFetcher', 'KuaidailiFetcher'),
    ('www.goubanjia.com', 'GoubanjiaFetcher', 'GoubanjiaFetcher'),
    ('www.66ip.cn', 'IP66Fetcher', 'IP66Fetcher'),
    ('www.ip3366.net', 'IP3366Fetcher', 'IP3366Fetcher'),
    ('ip.jiangxianli.com', 'JiangxianliFetcher', 'JiangxianliFetcher'),
    ('ip.ihuan.me', 'IHuanFetcher', 'IHuanFetcher'),
    ('www.proxyscan.io', 'ProxyscanFetcher', 'ProxyscanFetcher'),
    ('www.89ip.cn', 'IP89Fetcher', 'IP89Fetcher'),
    ('www.kxdaili.com', 'KaiXinFetcher', 'KaiXinFetcher'),
    ('www.xiladaili.com', 'XiLaFetcher', 'XiLaFetcher'),
    ('www.xsdaili.cn', 'XiaoShuFetcher', 'XiaoShuFetcher'),
    ('www.proxy-list.download', 'ProxyListFetcher', 'ProxyListFetcher'),
    ('proxyscrape.com', 'ProxyScrapeFetcher', 'ProxyScrapeFetcher'),
]

fetchers = []
for name, module_name, class_name in _FETCHER_SPECS:
    try:
        module = importlib.import_module(f'.{module_name}', __name__)
        fetcher_class = getattr(module, class_name)
        fetchers.append(Fetcher(name=name, fetcher=fetcher_class))
    except Exception as err:
        _logger.warning(
            'Skip fetcher %s, unable to import %s.%s: %s',
            name,
            module_name,
            class_name,
            err
        )
