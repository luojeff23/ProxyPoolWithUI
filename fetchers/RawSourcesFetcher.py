# encoding: utf-8

import os
import re
import logging
import requests

from .BaseFetcher import BaseFetcher


class RawSourcesFetcher(BaseFetcher):
    """
    从配置文件读取 raw 文本代理源（每行一个 source），解析 ip:port。

    sources 文件格式：
    1. protocol,url
       例如：http,https://example.com/http.txt
    2. url（未显式指定协议时默认按 http 处理）
    支持 protocol: http/https/socks4/socks5/auto
    """

    _LINE_RE = re.compile(
        r'(?:(http|https|socks4|socks5)://)?'
        r'(\d{1,3}(?:\.\d{1,3}){3})'
        r':(\d{1,5})',
        re.IGNORECASE
    )

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sources_file = os.getenv(
            'RAW_SOURCES_FILE',
            os.path.join(os.path.dirname(__file__), '..', 'sources', 'raw_sources.txt')
        )
        self.request_timeout = int(os.getenv('RAW_SOURCES_TIMEOUT', '8'))

    @staticmethod
    def _valid_ipv4(ip):
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            values = [int(part) for part in parts]
        except ValueError:
            return False
        return all(0 <= value <= 255 for value in values)

    @staticmethod
    def _normalize_protocol(protocol, default_protocol):
        p = (protocol or default_protocol or 'http').strip().lower()
        if p in ('http', 'https', 'socks4', 'socks5'):
            return p
        if p == 'auto':
            return 'http'
        return 'http'

    def _load_sources(self):
        sources = []
        if not os.path.exists(self.sources_file):
            self.logger.warning('raw sources file not found: %s', self.sources_file)
            return sources

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if len(line) == 0 or line.startswith('#'):
                    continue
                if ',' in line:
                    protocol, url = line.split(',', 1)
                    protocol = protocol.strip().lower()
                    url = url.strip()
                else:
                    protocol, url = 'http', line
                if len(url) > 0:
                    sources.append((protocol, url))
        return sources

    def _parse_text(self, text, source_protocol):
        proxies = []
        for match in self._LINE_RE.finditer(text):
            inline_protocol = match.group(1)
            ip = match.group(2)
            port_raw = match.group(3)

            if not self._valid_ipv4(ip):
                continue

            try:
                port = int(port_raw)
            except ValueError:
                continue

            if port <= 0 or port > 65535:
                continue

            protocol = self._normalize_protocol(inline_protocol, source_protocol)
            proxies.append((protocol, ip, port))
        return proxies

    def fetch(self):
        all_proxies = []
        for protocol, url in self._load_sources():
            try:
                resp = requests.get(url, timeout=self.request_timeout)
                resp.raise_for_status()
                all_proxies.extend(self._parse_text(resp.text, protocol))
            except Exception as err:
                self.logger.error('raw source fetch failed: %s, %s', url, err)

        # 去重，保证返回格式符合项目要求
        return list(set(all_proxies))
