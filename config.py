# encoding: utf-8

"""
配置文件，一般来说不需要修改
如果需要启用或者禁用某些网站的爬取器，可在网页上进行配置
"""

import os

def _get_int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def _get_str_env(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == '':
        return default
    return value

# 数据库文件路径
DATABASE_PATH = _get_str_env(
    'DATABASE_PATH',
    os.path.join(os.path.dirname(__file__), 'data.db')
)

# API监听配置
# 出于安全考虑，默认仅监听本地回环地址，避免误暴露到局域网/公网
API_HOST = _get_str_env('API_HOST', '127.0.0.1')
API_PORT = _get_int_env('API_PORT', 5000)

# 每次运行所有爬取器之后，睡眠多少时间，单位秒
PROC_FETCHER_SLEEP = _get_int_env('PROC_FETCHER_SLEEP', 5 * 60)

# 验证器每次睡眠的时间，单位秒
PROC_VALIDATOR_SLEEP = _get_int_env('PROC_VALIDATOR_SLEEP', 5)

# 验证器的配置参数
VALIDATE_THREAD_NUM = _get_int_env('VALIDATE_THREAD_NUM', 200) # 验证线程数量
# 验证器的逻辑是：
# 使用代理访问 VALIDATE_URL 网站，超时时间设置为 VALIDATE_TIMEOUT
# 如果没有超时：
# 1、若选择的验证方式为GET：  返回的网页中包含 VALIDATE_KEYWORD 文字，那么就认为本次验证成功
# 2、若选择的验证方式为HEAD： 返回的响应头中，对于的 VALIDATE_HEADER 响应字段内容包含 VALIDATE_KEYWORD 内容，那么就认为本次验证成功
# 上述过程最多进行 VALIDATE_MAX_FAILS 次，只要有一次成功，就认为代理可用
VALIDATE_URL = _get_str_env('VALIDATE_URL', 'http://example.com')
VALIDATE_METHOD = _get_str_env('VALIDATE_METHOD', 'GET').upper() # 验证方式，可选：GET、HEAD
VALIDATE_HEADER = _get_str_env('VALIDATE_HEADER', 'location') # 仅用于HEAD验证方式
VALIDATE_KEYWORD = _get_str_env('VALIDATE_KEYWORD', 'Example Domain')
VALIDATE_TIMEOUT = _get_int_env('VALIDATE_TIMEOUT', 5) # 超时时间，单位s
VALIDATE_MAX_FAILS = _get_int_env('VALIDATE_MAX_FAILS', 3)
