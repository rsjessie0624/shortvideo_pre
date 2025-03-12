import os
import requests
import time
import json
import re
from utils import sanitize_filename, random_sleep

class Downloader:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 加载cookie
        self._load_cookies()
        
    def _load_cookies(self):
        """加载平台Cookie"""
        cookie_files = {
            'douyin': os.path.join(self.config.cookies_dir, 'douyin_cookies.json'),
            'xiaohongshu': os.path.join(self.config.cookies_dir, 'xiaohongshu_cookies.json'),
            'kuaishou': os.path.join(self.config.cookies_dir, 'kuaishou_cookies.json'),
            'weixin': os.path.join(self.config.cookies_dir, 'weixin_cookies.json')
        }
        
        for platform, cookie_file in cookie_files.items():
            if os.path.exists(cookie_file):
                try:
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    
                    # 设置cookie到会话
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
                    
                    print(f"已加载{platform}平台的Cookie")
                except Exception as e:
                    print(f"加载{platform}平台Cookie失败: {e}")
    
    def save_cookies(self, platform):
        """保存当前会话的Cookie"""
        cookie_file = os.path.join(self.config.cookies_dir, f'{platform}_cookies.json')
        
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': cookie.expires,
                'secure': cookie.secure,
            })
        
        try:
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f)
            print(f"{platform}平台Cookie已保存")
            return True
        except Exception as e:
            print(f"保存{platform}平台Cookie失败: {e}")
            return False
            
    def update_headers(self, platform):
        """根据平台更新请求头"""
        if platform == 'douyin':
            self.session.headers.update({
                'Referer': 'https://www.douyin.com/',
                'Origin': 'https://www.douyin.com'
            })
        elif platform == 'xiaohongshu':
            self.session.headers.update({
                'Referer': 'https://www.xiaohongshu.com/',
                'Origin': 'https://www.xiaohongshu.com'
            })
        elif platform == 'kuaishou':
            self.session.headers.update({
                'Referer': 'https://www.kuaishou.com/',
                'Origin': 'https://www.kuaishou.com'
            })
        elif platform == 'weixin':
            self.session.headers.update({
                'Referer': 'https://channels.weixin.qq.com/',
                'Origin': 'https://channels.weixin.qq.com'
            })
    
    def download_file(self, url, save_path, chunk_size=8192):
        """下载文件到指定路径"""
        try:
            response = self.session.get(url, stream=True, timeout=self.config.get('timeout'))
            response.raise_for_status()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # 保存文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
    
    def download_douyin_video(self, video_id, title=None):
        """下载抖音视频"""
        # 构建API请求URL
        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
        
        try:
            # 更新请求头
            self.update_headers('douyin')
            
            # 获取视频信息
            response = self.session.get(api_url, timeout=self.config.get('timeout'))
            response.raise_for_status()
            
            data = response.json()
            
            # 检查是否需要登录
            if 'status_code' in data and data['status_code'] != 0:
                if data.get('status_msg') == 'need_login':
                    return {'success': False, 'need_login': True, 'message': '需要登录才能获取视频信息'}
                return {'success': False, 'message': data.get('status_msg', '获取视频信息失败')}
            
            # 提取视频信息
            item_list = data.get('item_list', [])
            if not item_list:
                return {'success': False, 'message': '未找到视频信息'}
            
            item = item_list[0]
            
            # 获取视频标题
            video_title = title or item.get('desc', f'douyin_video_{video_id}')
            video_title = sanitize_filename(video_title)
            
            # 获取视频URL
            video_url = None
            video_data = item.get('video', {})
            play_addr = video_data.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            
            if url_list:
                # 优先选择无水印版本
                for url in url_list:
                    if 'aweme.snssdk.com' in url:
                        video_url = url
                        break
                
                # 如果没找到无水印版本，使用第一个链接
                if not video_url:
                    video_url = url_list[0]
            
            if not video_url:
                return {'success': False, 'message': '未找到视频下载链接'}
            
            # 下载视频
            download_path = self.config.get('download_path')
            video_path = os.path.join(download_path, f"{video_title}.mp4")
            
            if self.download_file(video_url, video_path):
                return {
                    'success': True,
                    'message': '视频下载成功',
                    'video_path': video_path,
                    'video_info': item
                }
            else:
                return {'success': False, 'message': '视频下载失败'}
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'网络请求异常: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'下载抖音视频失败: {str(e)}'}
    
    def download_video(self, platform, video_id, title=None):
        """根据平台下载视频"""
        if platform == 'douyin':
            return self.download_douyin_video(video_id, title)
        elif platform == 'xiaohongshu':
            # 目前优先实现抖音，其他平台类似实现
            return {'success': False, 'message': '小红书视频下载功能开发中'}
        elif platform == 'kuaishou':
            return {'success': False, 'message': '快手视频下载功能开发中'}
        elif platform == 'weixin':
            return {'success': False, 'message': '微信视频号下载功能开发中'}
        else:
            return {'success': False, 'message': '不支持的平台'}