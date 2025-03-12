import os
import re
import requests
import time
import random
from urllib.parse import urlparse, parse_qs

def sanitize_filename(filename):
    """将字符串转换为有效的文件名"""
    # 替换无效字符
    invalid_chars = r'[\\/*?:"<>|]'
    sanitized = re.sub(invalid_chars, "", filename)
    
    # 限制长度
    if len(sanitized) > 50:
        sanitized = sanitized[:47] + "..."
        
    return sanitized.strip()

def extract_url_from_text(text):
    """从文本中提取URL"""
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def follow_redirects(url, max_redirects=5):
    """跟随URL重定向，获取最终URL"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"跟随重定向失败: {e}")
        return url

def random_sleep(min_seconds=1, max_seconds=3):
    """随机休眠一段时间，避免请求过快"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)

def format_number(num):
    """格式化数字，处理例如"1.2w"这样的格式"""
    if isinstance(num, str):
        if 'w' in num or '万' in num:
            num = num.replace('w', '').replace('万', '')
            try:
                return float(num) * 10000
            except:
                return 0
        elif 'k' in num:
            num = num.replace('k', '')
            try:
                return float(num) * 1000
            except:
                return 0
    
    try:
        return int(num)
    except:
        return 0

def get_domain_from_url(url):
    """从URL中提取域名"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def is_douyin_url(url):
    """判断是否为抖音链接"""
    return "douyin.com" in url or "iesdouyin.com" in url

def is_xiaohongshu_url(url):
    """判断是否为小红书链接"""
    return "xiaohongshu.com" in url or "xhslink.com" in url

def is_kuaishou_url(url):
    """判断是否为快手链接"""
    return "kuaishou.com" in url or "gifshow.com" in url

def is_weixin_url(url):
    """判断是否为微信视频号链接"""
    return "weixin.qq.com" in url or "wx.qq.com" in url