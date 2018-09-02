# coding = utf-8

import requests
import os
from bs4 import BeautifulSoup
import byrtorrent
import time

'''
北邮人PT自动下载脚本
自动下载免费文件 调用系统默认BT客户端打开 
保存已经下载的id 避免重复
'''


class Torrent(object):
    __attrs__ = [
        '_content', 'title', 'seed_id', 'detail_url', 'download_url',
        'comments_num', 'upload_time', 'file_size', 'seeders_num',
        'leechers_num', 'snatched_num',
    ]

    def __init__(self, content):
        self._content = content
        self.title = None
        self.seed_id = None
        self.detail_url = None
        self.download_url = None
        self.comments_num = None
        self.upload_time = None
        self.file_size = None
        self.seeders_num = None  # 做种数
        self.leechers_num = None  # 下载数
        self.snatched_num = None  # 完成数

    def parse(self):
        contents = self._content.contents
        link = contents[3].table.tr.td.a
        self.title = link.get("title")
        self.seed_id = link.get("href").split("id=")[1].split("&")[0]
        self.detail_url = "https://bt.byr.cn/details.php?id=" + self.seed_id
        self.download_url = "https://bt.byr.cn/download.php?id=" + self.seed_id
        self.comments_num = contents[4].a.contents[0]
        self.upload_time = contents[5].span.get("title")  # 上传时间 2018-09-01 12:12:20
        self.file_size = contents[6].contents[0] + " " + contents[6].contents[2]
        self.seeders_num = contents[7].b.a.contents[0]
        if contents[9].contents[0] == '0':
            self.leechers_num = 0
        else:
            self.leechers_num = contents[9].b.a.contents[0]
        if contents[11].contents[0] == '0':
            self.snatched_num = 0
        else:
            self.snatched_num = contents[11].a.b.contents[0]


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
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://bt.byr.cn/torrents.php?secocat=&cat=&spstate=2"
    cookies = get_cookie()
    r = requests.get(url=url, headers=headers, cookies=cookies)
    data = r.text
    soup = BeautifulSoup(data, 'html.parser')

    items = soup.find(attrs={"class": "torrents"}).contents[0].find_all("tr", attrs={"class": "free_bg"},
                                                                        recursive=False)
    torrents = []
    for item in items:
        torrent = byrtorrent.Torrent(item)
        torrent.parse()
        torrents.append(torrent)

    return torrents


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


# 排序 获取最佳的seed_torrent
def sort_torrents_list(torrents):
    latest_time = 0.0
    latest_torrent = None
    downed_lines = view_down_log()
    print(downed_lines)
    for torrent in torrents:
        if downed_lines is not None and torrent.seed_id in downed_lines:
            continue
        ts = time.strptime(torrent.upload_time, "%Y-%m-%d %H:%M:%S")
        time_staps = time.mktime(ts)
        if time_staps > latest_time:
            latest_time = time_staps
            latest_torrent = torrent
    return latest_torrent


# 下载文件并启动系统默认BT客户端打开该文件
def download_torrent(torrent):
    title = str(torrent.title)
    if len(title) >= 180:
        title = title[0:179]

    remove_list = "?><\/:\"*|"
    for ch in remove_list:
        if ch in title:
            title = title.replace(ch, "")
    print(title)
    filename = "./data/seeds/" + title + ".torrent"

    headers = {'User-Agent': 'Mozilla/5.0'}
    cookies = get_cookie()
    r = requests.get(url=torrent.download_url, headers=headers, cookies=cookies)
    with open(filename, "wb") as f:
        f.write(r.content)

    # 保存到记录文件中
    save_down_log(torrent.seed_id)

    os.startfile(os.getcwd() + filename)


def main():
    torrents = get_torrents_list()
    latest_torrent = sort_torrents_list(torrents)
    download_torrent(latest_torrent)


if __name__ == '__main__':
    main()
