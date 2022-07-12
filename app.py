"""
    @Author: ImYrS Yang
    @Date: 2022/7/12
    @Copyright: ImYrS Yang
    @Description: 
"""

import os
import re
from time import sleep
from typing import Optional
from threading import Thread

import keyboard
import pyperclip
from plyer import notification
import requests

from config import SHLINK_ENDPOINT as ENDPOINT, API_KEY as KEY

PATTERN = re.compile(
    r"^((https|http|ftp|rtsp|mms)?://)"
    r"?(([0-9a-z_!~*'().&=+$%-]+: )?[0-9a-z_!~*'().&=+$%-]+@)?"  # ftp 的 user@
    r"(([0-9]{1,3}\.){3}[0-9]{1,3}"  # IP
    r"|"  # 允许 IP 和 DOMAIN
    r"([\da-zA-Z_!~*'()-]+\.)*"  # 域名
    r"([\da-zA-Z][\da-z-]{0,61})?[\da-z]\."  # 二级域名
    r"[a-z]{2,6})"  # 一级域名
    r"(:\d{1,5})?"  # 端口
    r"((/?)|"  # 最后一个 / 或空
    r"(/[\da-zA-Z_!~*'().;?:@&=+$,%#-]+)+/?)$"  # 路径
)  # 匹配 URL
COPIED = ''  # 剪贴板上一次的内容


def main():
    """
    主函数

    - 移除特殊字符
    - 自动补全 HTTP 协议头
    - 正则匹配复制内容
    - 生成短链接
    :return:
    """
    data = pyperclip.paste().strip().strip('\n').strip('\r').strip('\t')
    data = 'http://' + data if not data.startswith('http') else data
    if PATTERN.match(data):
        url = create(data)
        if url:
            global COPIED
            COPIED = url
            pyperclip.copy(url)
            notify('短链接已生成并复制', f'新链接: {url}\n原链接: {data[:100]}')


def monitor():
    """
    监控剪贴板的变动
    :return:
    """
    global COPIED
    while True:
        sleep(0.2)
        if pyperclip.paste() != COPIED:
            COPIED = pyperclip.paste()
            main()


def create(url: str) -> Optional[str]:
    """
    生成短链接
    :param url: 长链接
    :return: 生成成功时返回短链接, 否则返回 None
    """
    try:
        r = requests.post(
            f'{ENDPOINT}/rest/v2/short-urls',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'x-api-key': KEY,
            },
            json={
                'longUrl': url,
            },
        )
        r.raise_for_status()

        return r.json()['shortUrl']
    except requests.RequestException as e:
        notify('请求 API 失败', str(e))
    except Exception as e:
        notify('生成短链接错误', str(e))
    return None


def notify(title, message: Optional[str] = None, timeout: Optional[int] = 2):
    """
    显示通知
    :param title: 标题
    :param message: 消息
    :param timeout: 延迟时间
    :return:
    """
    notification.notify(
        title=title,
        message=message,
        timeout=timeout,
    )


def stop():
    notify('Shlink 已退出', '再见')
    exit(0)


if __name__ == '__main__':
    os.environ['NO_PROXY'] = '*'

    try:
        notify('Shlink 已启动', '请按 Ctrl + Shift + Alt + E 退出')

        mt = Thread(target=monitor)  # 启动监控线程
        mt.daemon = True
        mt.start()

        keyboard.wait('ctrl+shift+alt+e')
        # 检测到 Ctrl + Shift + Alt + E 时退出
        stop()
    except Exception as e:
        notify('Shlink 发生错误, 自动退出', str(e))
        exit(1)
