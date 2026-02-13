# 简易好用的免费代理池

[![](https://img.shields.io/badge/python-3.10+-brightgreen)](https://github.com/OxOOo/ProxyPoolWithUI)

兼容系统：
![Windows](https://img.shields.io/badge/Windows-o-brightgreen)
![Linux](https://img.shields.io/badge/Linux-o-brightgreen)
![MacOS](https://img.shields.io/badge/MacOS-o-brightgreen)

* 定时自动爬取网络上的免费代理
* 定时对代理进行验证，集成API随时返回可用代理
* 不需要第三方数据库支持，一键启动，简单易用
* 集成WEB管理界面，方便查看代理状态并对代理池进行配置
* 拥有详细的注释，可以非常方便地学习或修改

推荐:
* [HTTP代理原理](https://zhuanlan.zhihu.com/p/349028243)

项目Demo：[http://chenyu0x00.com:8888/](http://chenyu0x00.com:8888/)

**2021年3月8日测试，项目运行半小时后，支持访问HTTPS的代理有40+，支持访问HTTP的代理有100+。**

如果你知道有好用的代理源，或者是发现本项目存在一些问题，欢迎通过Issues和我们讨论。

## WEB管理界面截图

![screenshot1](docs/screenshot1.png)
![screenshot2](docs/screenshot2.png)

## 已经集成的免费代理源

| 名称         | 地址                           |备注          |
|--------------|-------------------------------|-------------|
| 悠悠网络代理   | https://uu-proxy.com/         |              |
| 快代理       | https://www.kuaidaili.com/     |              |
| 全网代理     | http://www.goubanjia.com/      |              |
| 66代理       | http://www.66ip.cn/            |              |
| 云代理       | http://www.ip3366.net/         |              |
| 免费代理库   | https://ip.jiangxianli.com/     |              |
| 小幻HTTP代理 | https://ip.ihuan.me/            |              |
| 89免费代理   | https://www.89ip.cn/            |              |
| ProxyScan   | https://www.proxyscan.io/      |              |
| 开心代理     | http://www.kxdaili.com/         |              |
| 西拉代理     | http://www.xiladaili.com/       |              |
| 小舒代理     | http://www.xsdaili.cn/          |              |
| ProxyList   | https://www.proxy-list.download/|              |
| ProxyScrape | https://proxyscrape.com/        |国内无法直接访问 |

## 运行本项目

本项目目前只适配了Python3，建议使用Python 3.10~3.12。

1. 下载代码

```bash
git clone https://github.com/OxOOo/ProxyPoolWithUI.git
```

2. 安装Python依赖(在`ProxyPoolWithUI`目录下执行)

```bash
python -m venv .venv
# Windows:
# .\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

依赖安装受限时，系统会自动跳过无法导入的爬取器（日志中会出现`Skip fetcher ...`），其余可用爬取器仍可继续工作。

如果你需要启用依赖`pyquery`的网页解析型爬取器，再额外安装：

```bash
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-html-fetchers.txt
```

如果你在Windows上使用本地代理（如`127.0.0.1:7890`），可使用一键脚本（推荐）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_with_proxy.ps1 -InstallDeps
```

该脚本会为当前进程注入代理环境变量并启动项目。
如需在项目内虚拟环境中运行，可追加参数`-UseVenv`。
如果要额外安装网页解析型爬取器依赖，可使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_with_proxy.ps1 -UseVenv -InstallDeps -InstallHtmlFetchers
```

3. 启动(在`ProxyPoolWithUI`目录下执行)

```bash
python main.py
```

或使用脚本启动（自动注入`HTTP_PROXY/HTTPS_PROXY`）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_with_proxy.ps1
```

也可双击运行：

```text
scripts\run_with_proxy.cmd
```

如果你在运行了上述命令之后，在命令行中看到了类似如下截图，那么说明项目成功启动了：

![term](docs/term.png)

4. 使用浏览器打开`http://127.0.0.1:5000`，可以看到WEB管理界面。

## Docker构建项目

1. 下载项目文件

```bash
git clone https://github.com/OxOOo/ProxyPoolWithUI.git
cd ProxyPoolWithUI
```

2. 构建docker镜像

```bash
docker build --tag proxy_pool .
```

3. 运行镜像

```bash
docker run -p 5000:5000 -v /root/ProxyPoolWithUI:/proxy -d proxy_pool
```
`/root/ProxyPoolWithUI`为clone下来的项目目录路径，请自行更改

如果你希望容器对外提供服务，可显式设置：

```bash
docker run -p 5000:5000 -e API_HOST=0.0.0.0 -v /root/ProxyPoolWithUI:/proxy -d proxy_pool
```


## 使用代理

1. API接口

项目启动之后，会自动爬取并检测代理是否可用，因此我们只需要关注如何使用代理即可。

* `http://localhost:5000/fetch_random` : 随机获取一个可用代理，如果没有可用代理则返回空白
  
  返回示例 : `http://127.0.0.1:8080`

* `http://localhost:5000/fetch_all` : 获取所有可用代理，如果没有可用代理则返回空白
  
  返回示例 : `http://127.0.0.1:8080,http://127.0.0.1:8081`

1. 使用代理

不同语言使用代理的方式各不相同，这里提供一个Python集成本项目并使用代理的示例代码：

```python
# encoding : utf-8

import requests

def main():
    proxy_uri = requests.get('http://localhost:5000/fetch_random').text
    if len(proxy_uri) == 0:
        print(u'暂时没有可用代理')
        return
    print(u'获取到的代理是：' + proxy_uri)
    
    proxies = { 'http': proxy_uri }
    html = requests.get('http://www.baidu.com', proxies=proxies).text
    if u'百度一下，你就知道' in html:
        print('代理可用')
    else:
        print('代理不可用')

if __name__ == '__main__':
    main()
```

## 配置

如果是需要禁用或者启用某些代理，可直接在WEB管理界面进行操作。

本项目的大部分配置均可在`config.py`中找到，默认配置已经可以适应绝大部分情况，一般来说不需要进行修改。

其中常用环境变量包括：

* `API_HOST`：API监听地址，默认`127.0.0.1`（仅本机可访问）
* `API_PORT`：API端口，默认`5000`
* `VALIDATE_URL`/`VALIDATE_METHOD`/`VALIDATE_KEYWORD`：验证策略相关配置
* `RAW_SOURCES_FILE`：`RawSourcesFetcher`代理源文件路径（默认`sources/raw_sources.txt`）
* `RAW_SOURCES_TIMEOUT`：`RawSourcesFetcher`请求超时时间（秒）

## 安全建议

* 学习和调试建议优先在本地运行，并保持`API_HOST=127.0.0.1`。
* 免费代理存在劫持、污染和失效风险，不要用于登录、支付、隐私数据传输。
* 若部署到Linux服务器，请至少配置防火墙、反向代理和访问控制，不要直接裸露接口到公网。

## 添加新的代理源

本项目的爬取器均在`fetchers`目录下，你也可以根据自己的需求对其中的爬取器进行修改或者扩展。

项目已内置`RawSourcesFetcher`（无`pyquery`依赖），会读取`sources/raw_sources.txt`中的源：

```text
http,https://example.com/http.txt
socks5,https://example.com/socks5.txt
```

每行一个源，支持格式：

* `protocol,url`
* `url`（默认按`http`处理）

其中`protocol`可选：`http`/`https`/`socks4`/`socks5`/`auto`。

编写本项目的爬取器并不复杂，详细的操作步骤可见[此处](fetchers/)，可以参考`fetchers`目录下已有的爬取器。

## 项目工作流程图

本项目主要包含三部分：

1. 爬取进程：主要包括`fetchers`目录和`proc/run_fetcher.py`文件
2. 验证进程：主要在`proc/run_validator.py`文件中
3. WEB与API：在`api`目录下

本项目的大致逻辑图如下：

注：为了便于理解与画图，下图的逻辑是经过简化之后的逻辑，详细过程可查看代码以及相应的注释。

![workflow](docs/workflow.png)

更详细的流程图见：[`docs/architecture.md`](docs/architecture.md)。

## 验证算法相关

1. 如何验证代理可用

目前验证代理可用的算法较为简单，核心思想是使用`requests`库访问一个指定网页，查看是否访问成功。

相关配置参数（包括`超时时间`，`尝试次数`等）可在`config.py`中找到，具体代码逻辑在`proc/run_validator.py`中。

2. 什么时候该验证哪个代理

这个问题比较复杂，很难有一个完美的解决方案，因此目前的算法较为简单，勉强可用，可在[db](db)目录下找到对于目前算法的说明。

如果你有更好的算法，欢迎通过Issues和我们讨论，也可以根据[db](db)目录下的[README](db/README.md)文件对代码进行修改。
