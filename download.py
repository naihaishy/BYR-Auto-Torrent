# coding = utf-8

import requests
import os
import time
import torrent as byr
import win32api
import win32con
import ctypes
import platform

'''
北邮人PT自动下载脚本
自动下载免费文件 调用系统默认BT客户端打开 
保存已经下载的id 避免重复
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


# 查看是否已经下载过了
def view_down_log():
    log_file = "./data/index.json"
    if not os.path.exists(log_file):
        return
    else:
        with open("./data/index.json", "r") as f:
            lines = f.readlines()

            log_lines = [line.replace("\n", "") for line in lines]
            return log_lines


# 保存已经下载的torrent
def save_down_log(seed_id):
    log_file = "./data/index.json"
    if not os.path.exists(log_file):
        f = open(log_file, "x")
        f.write(seed_id + "\n")
        f.close()
    else:
        downed_lines = view_down_log()
        if downed_lines is not None and seed_id in downed_lines:
            return
        else:
            f = open(log_file, "a")
            f.write(seed_id + "\n")
            f.close()


# 排序 获取最佳的seed_torrent 最佳策略为:时间最新->种子数最少->下载数最多
def sort_torrents_list(torrents):
    byr.BYRTorrents.sort_by_seed_rate(torrents, True)
    return torrents[0]


# 下载文件并启动系统默认BT客户端打开该文件
def download_torrent(torrent):

    # 处理文件名以及路径
    title = str(torrent.title)
    if len(title) >= 180:
        title = title[0:179]

    remove_list = "?><\/:\"*|"
    for ch in remove_list:
        if ch in title:
            title = title.replace(ch, "")
    filename = "./data/seeds/" + title + ".torrent"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
               'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}

    cookies = get_cookie()
    r = requests.get(url=torrent.download_url, headers=headers, cookies=cookies)
    with open(filename, "wb") as f:
        f.write(r.content)

    # 打开v6 speed软件
    os.startfile(os.getcwd() + filename)

    time.sleep(3)
    # 模拟Enter按键操作
    win32api.keybd_event(13, 0, 0, 0)
    win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)

    # 保存到记录文件中
    save_down_log(torrent.seed_id)


# 获取某个磁盘的剩余空间大小 GB
def get_free_space_gb(folder):
    """ Return folder/drive free space (in GB)
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value/1024/1024/1024
    else:
        st = os.statvfs(folder)
        return st.f_bavail * st.f_frsize/1024/1024


# 该函数依赖库有win10toast和pypiwin32
def inform_windows(torrent):
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toaster.show_toast("BYRBT免费种子上传通知",
                       "有人上传了最新了免费种子{title}".format(title=torrent.title),
                       icon_path="./data/favicon.ico",
                       duration=30,
                       threaded=True)


def other():
    torrents = get_torrents_list()
    if torrents is None:
        print("没有获取任何种子...")
        return
    byr.BYRTorrents.sort_by_time(torrents, True)

    latest_torrent = torrents[0]  # 最新的一个免费种子

    # 在5分钟内产生的免费torrent
    if time.time() - latest_torrent.time() < 60 * 5:
        print("最佳种子id为: " + str(latest_torrent.seed_id) + " 种子数: " + str(latest_torrent.seeders_num)
              + " 下载数: " + str(latest_torrent.leechers_num))

        if latest_torrent.seed_rate() < 0.1:
            print("下载做种比率太高,不下载")
            return

        # 磁盘空间
        free_space = get_free_space_gb('P:\\')  # GB
        if free_space < 30 or latest_torrent.size() > free_space * 1024:
            print("磁盘空间不足,不下载")
            return

        print("开始下载")
        download_torrent(latest_torrent)


def main():
    print("开启检测BYT " + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    torrents = get_torrents_list()

    if torrents is None:
        print("没有获取任何种子...")
        return

    byr.BYRTorrents.sort_by_time(torrents, True)

    latest_torrent = torrents[0]  # 最新的一个免费种子

    # 在5分钟内产生的免费torrent
    if time.time() - latest_torrent.time() < 60 * 2:
        inform_windows(latest_torrent)

        # 磁盘空间
        free_space = get_free_space_gb('P:\\')  # GB
        if free_space < 30 or latest_torrent.size() > free_space*1024:
            print("磁盘空间不足,不下载")
            return
        print("开始下载")
        download_torrent(latest_torrent)


if __name__ == '__main__':
    while 1:
        main()
        time.sleep(60 * 1)
