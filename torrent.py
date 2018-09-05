# coding = utf-8

import requests
from bs4 import BeautifulSoup
import time

"""
北邮人单个种子解析类
传入html tag 示例格式见seed.html
"""


class Torrent(object):
    __attrs__ = [
        '_content', 'title', 'seed_id', 'detail_url', 'download_url',
        'comments_num', 'upload_time', 'file_size', 'seeders_num',
        'leechers_num', 'snatched_num',
    ]

    # 传入的content是html tag <tr class="free_bg">.....</tr> 这包含了一个种子的所有信息 示例格式见seed.html
    def __init__(self, content):
        self._content = content
        self.title = None
        self.seed_id = 0
        self.detail_url = None
        self.download_url = None
        self.comments_num = None
        self.upload_time = None
        self.file_size = None
        self.seeders_num = 0  # 做种数
        self.leechers_num = 0  # 下载数
        self.snatched_num = 0  # 完成数
        self._red_seed = False  # 是否是红色种子

    def parse(self):
        contents = self._content.contents
        link = contents[3].table.tr.td.a
        self.title = link.get("title")
        self.seed_id = link.get("href").split("id=")[1].split("&")[0]
        self.detail_url = "https://bt.byr.cn/details.php?id=" + self.seed_id
        self.download_url = "https://bt.byr.cn/download.php?id=" + self.seed_id
        self.upload_time = contents[5].span.get("title")  # 上传时间 2018-09-01 12:12:20
        self.file_size = contents[6].contents[0] + " " + contents[6].contents[2]

        # 评论数有两种情况
        # 1.为0  <a href=" " title=" ">0</a>
        # 2.正常 <b><a href=" ">4</a></b>
        if contents[4].a.contents[0] == '0':
            # case 1
            self.comments_num = 0
        else:
            # case 2
            self.comments_num = int(str(contents[4].b.a.contents[0]).replace(",", ""))

        # 种子数三种情况
        # 1.红色不为0 <b><a href=" "><font color="#550000">1</font></a></b>
        # 2.红色为0  <span class="red">0</span>
        # 3.正常 <<b><a href=" ">45</a></b>
        if str(contents[7].contents[0]).find("pan") == 2:
            # case 2
            self.seeders_num = 0
            self._red_seed = True  # 大量下载但是种子不足时显示为红色
        elif str(contents[7].b.a.contents[0]).find("ont") == 2:
            # case 1
            self.seeders_num = int(str(contents[7].b.a.font.contents[0]).replace(",", ""))  # 三位计数转换为int 1,234=>1234
        else:
            # case 3
            self.seeders_num = int(str(contents[7].b.a.contents[0]).replace(",", ""))

        # 下载数有两种情况
        # 1.为0  0
        # 2.正常 <b><a href=" ">3</a></b>
        if contents[9].contents[0] == '0':
            # case 1
            self.leechers_num = 0
        else:
            # case 2
            self.leechers_num = int(str(contents[9].b.a.contents[0]).replace(",", ""))

        # 完成数有两种情况
        # 1.为0  0
        # 2.正常 <a href=" "><b>7</b></a>
        if contents[11].contents[0] == '0':
            # case 1
            self.snatched_num = 0
        else:
            # case 2
            self.snatched_num = int(str(contents[11].a.b.contents[0]).replace(",", ""))

    def time(self):
        return time.mktime(time.strptime(self.upload_time, "%Y-%m-%d %H:%M:%S"))

    def size(self):
        """最小单位为MB 最大单位为TB"""
        items = str(self.file_size).split(" ")
        if items[1] == 'TB':
            return float(items[0]) * 1024 * 1024  # 换算为MB
        if items[1] == 'GB':
            return float(items[0]) * 1024  # 换算为MB
        if items[1] == 'MB':
            return float(items[0])  # 换算为MB

    def seeders(self):
        return self.seeders_num

    def leechers(self):
        return self.leechers_num

    def snatchers(self):
        return self.snatched_num

    def seed_rate(self):
        if self.seeders_num is 0:
            return 9999.9
        elif self._red_seed:
            return 8888.8
        else:
            return self.leechers_num/float(self.seeders_num)


"""
北邮人PT 页面种子解析类
传入一个url返回该页面的所有种子信息
返回 List[Torrent]
"""


class PageTorrents(object):
    __attrs__ = [
        'url', 'cookie'
    ]

    def __init__(self, url, cookie):
        self.url = url
        self.cookie = cookie

    def parse(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
                   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}

        response = requests.get(url=self.url, headers=headers, cookies=self.cookie)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find(attrs={"class": "torrents"}).contents[0].find_all("tr", recursive=False)[1:]

        torrents = []
        for item in items:
            torrent = Torrent(item)
            torrent.parse()
            torrents.append(torrent)

        return torrents


"""
北邮人特定类型种子搜索
返回 List[Torrent]
"""


class BYRTorrents(object):

    byr_torrent_base_url = "https://bt.byr.cn/torrents.php?"

    @staticmethod
    def sort_by_time(torrents, reverse=False):
        """根据上传时间排序 默认升序"""
        torrents.sort(key=Torrent.time, reverse=reverse)

    @staticmethod
    def sort_by_size(torrents, reverse=False):
        """根据文件大小排序 默认升序"""
        torrents.sort(key=Torrent.size, reverse=reverse)

    @staticmethod
    def sort_by_seeders(torrents, reverse=False):
        """根据种子数目排序 默认升序"""
        torrents.sort(key=Torrent.seeders, reverse=reverse)

    @staticmethod
    def sort_by_leechers(torrents, reverse=False):
        """根据下载数目排序 默认升序"""
        torrents.sort(key=Torrent.leechers, reverse=reverse)

    @staticmethod
    def sort_by_snatchers(torrents, reverse=False):
        """根据完成种子数目排序 默认升序"""
        torrents.sort(key=Torrent.snatchers, reverse=reverse)

    @staticmethod
    def sort_by_seed_rate(torrents, reverse=False):
        """根据下载数与种子数比例排序 默认升序"""
        torrents.sort(key=Torrent.seed_rate, reverse=reverse)


"""
北邮人根据特定类型返回搜索参数项
返回 url paras
"""


class BYRUrlParas(object):

    def __init__(self, paras):
        """paras是个List"""
        self.paras = paras

    def movie(self):
        self.paras['cat'] = 408
        return self

    def tvserie(self):
        self.paras['cat'] = 401
        return self

    def cartoon(self):
        self.paras['cat'] = 404
        return self

    def music(self):
        self.paras['cat'] = 402
        return self

    def show(self):
        self.paras['cat'] = 405
        return self

    def game(self):
        self.paras['cat'] = 403
        return self

    def software(self):
        self.paras['cat'] = 406
        return self

    def docs(self):
        self.paras['cat'] = 407
        return self

    def sport(self):
        self.paras['cat'] = 409
        return self

    def record(self):
        self.paras['cat'] = 410
        return self

    def free_down(self):
        """免费下载"""
        self.paras['spstate'] = 2
        return self

    def double_up(self):
        """两倍上传"""
        self.paras['spstate'] = 3
        return self

    def free_down_double_up(self):
        """免费下载且两倍上传"""
        self.paras['spstate'] = 4
        return self

    def half_down(self):
        """50%下载"""
        self.paras['spstate'] = 5
        return self

    def half_down_double_up(self):
        """50%下载且两倍上传"""
        self.paras['spstate'] = 6
        return self

    def thirty_percent_down(self):
        """30%下载"""
        self.paras['spstate'] = 7
        return self
