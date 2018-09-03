# coding = utf-8

import time
import torrent as byr


'''
北邮人PT种子上传通知脚本
当有免费种子上传时第一时间通过email或者windows桌面toast通知
'''


# 读取cookie信息 登录后使用F12审查元素获取cookie
def get_cookie():
    f = open(r'./data/cookies.txt', 'r')
    cookies = {}
    for line in f.read().split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


# 获取50条免费的种子信息
def get_torrents_list():
    url = "https://bt.byr.cn/torrents.php?spstate=2"
    cookies = get_cookie()
    return byr.PageTorrents(url, cookies).parse()


# 通知
def inform_email(torrent):
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    body = """
    您好, BYRBT有最新的免费种子上传啦，赶紧去下载吧！！！</br>
    <h3>种子信息</h3>
    <p><strong>标题:</strong>{title}</p>
    <p><strong>大小:</strong>{size}</p>
    <p><strong>种子数:</strong>{seeders_num}</p>
    <p><strong>下载数:</strong>{leechers_num}</p>
    <p><strong>下载链接:</strong><a href='{download_url}'>点击下载种子文件</a></p>
    """.format(title=torrent.title, size=torrent.file_size, seeders_num=torrent.seeders_num,
               leechers_num=torrent.leechers_num, download_url=torrent.download_url)
    message = MIMEText(body, 'html', 'utf-8')  # 文本内容
    message['From'] = Header("Naihai<xxx@xxx.com>", 'utf-8')  # 发送者
    message['To'] = Header("xxx@xxx.com", 'utf-8')  # 接收者
    subject = 'BYRBT免费种子上传通知'  # 主题
    message['Subject'] = Header(subject, 'utf-8')

    smtp = smtplib.SMTP_SSL(host="smtp.xxx.com", port="465")

    try:
        smtp.login("xx@xx.com", "xxx")
        print("登录成功")
    except smtplib.SMTPException:
        print("登录失败")
        return
    try:
        smtp.sendmail(from_addr="xxx@xxx.com", to_addrs="xxx@xxx.com", msg=message.as_string())
        print("发送成功")
    except smtplib.SMTPException:
        print("发送失败")
        return


# 该函数依赖库有win10toast和pypiwin32
def inform_windows(torrent):
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast("BYRBT免费种子上传通知",
                       "有人上传了最新了免费种子{title}".format(title=torrent.title),
                       icon_path="./data/favicon.ico",
                       duration=10,
                       threaded=True)


def main():
    print("开启检测BYT " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    torrents = get_torrents_list()
    byr.BYRTorrents.sort_by_time(torrents, True)   # 最新的一个免费种子

    latest_torrent = torrents[0]
    # 转成时间戳
    ts = time.strptime(latest_torrent.upload_time, "%Y-%m-%d %H:%M:%S")
    time_staps = time.mktime(ts)

    # 在程序sleep期间内产生的torrent
    if time.time() - time_staps < 60 * 5:
        inform_email(latest_torrent)
        inform_windows(latest_torrent)


if __name__ == '__main__':
    # 每60s运行一次
    while 1:
        main()
        time.sleep(60 * 5)
