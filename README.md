## 北邮人PT自动下载脚本
### 自动下载免费文件 并且调用系统默认BT客户端打开

### 依赖库
    requests
    BeautifulSoup


### 使用说明

1. 登录北邮人BT

2. 使用F12审查元素
获取cookie信息[Network中获取request信息]
将cookie信息存入data/cookie.txt文件中
![获取cookie演示](https://raw.githubusercontent.com/naihaishy/BYR-Auto-Torrent/master/aa.png "cookie.png")

3. 执行该脚本
需要确保BT客户端满足北邮人PT要求
将该客户端设置为系统默认打开.torrent文件的应用


4. 默认下载最新的一个免费文件

