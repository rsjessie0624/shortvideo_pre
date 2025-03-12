import requests
import json
import re
import time
from bs4 import BeautifulSoup
from utils.common import logger

class ContentFetcher:
    def __init__(self, cookies=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.cookies = cookies if cookies else {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if self.cookies:
            self.session.cookies.update(self.cookies)
    
    def update_cookies(self, cookies):
        """更新cookies"""
        self.cookies.update(cookies)
        self.session.cookies.update(cookies)
    
    def check_login_status(self, response):
        """检查是否需要登录"""
        # 根据响应内容判断是否需要登录
        if '登录' in response.text and '密码' in response.text:
            return False
        return True
    
    def fetch_douyin_video_info(self, video_id, url):
        """获取抖音视频信息"""
        try:
            # 尝试直接获取视频页面
            response = self.session.get(url, timeout=10)
            
            # 检查是否需要登录
            login_required = not self.check_login_status(response)
            if login_required:
                logger.warning("Login required to access this video")
                return {'login_required': True}
            
            # 从网页内容中提取视频信息
            html_content = response.text
            
            # 提取视频信息的模式可能需要根据抖音网页结构调整
            # 尝试从HTML中提取JSON数据
            render_data_pattern = r'<script id="RENDER_DATA" type="application/json">(.*?)</script>'
            render_data_match = re.search(render_data_pattern, html_content)
            
            if render_data_match:
                json_data = render_data_match.group(1)
                # 解码URL编码的JSON
                import urllib.parse
                decoded_data = urllib.parse.unquote(json_data)
                data = json.loads(decoded_data)
                
                # 从解析的数据中提取视频信息
                # 注意：这里的路径需要根据实际的数据结构调整
                video_info = None
                for key in data:
                    if 'aweme' in key and 'detail' in data[key]:
                        video_info = data[key]['detail']
                        break
                
                if video_info:
                    # 提取有用的信息
                    result = {
                        'title': video_info.get('desc', ''),
                        'description': video_info.get('desc', ''),
                        'tags': [],
                        'stats': {
                            'likes': video_info.get('statistics', {}).get('digg_count', 0),
                            'comments': video_info.get('statistics', {}).get('comment_count', 0),
                            'favorites': video_info.get('statistics', {}).get('collect_count', 0),
                            'shares': video_info.get('statistics', {}).get('share_count', 0)
                        },
                        'author': {
                            'name': video_info.get('author', {}).get('nickname', ''),
                            'id': video_info.get('author', {}).get('unique_id', '')
                        },
                        'source_url': url,
                        'play_url': ''
                    }
                    
                    # 提取标签
                    if 'text_extra' in video_info:
                        for tag_info in video_info['text_extra']:
                            if 'hashtag_name' in tag_info and tag_info['hashtag_name']:
                                result['tags'].append(tag_info['hashtag_name'])
                    
                    # 提取视频播放地址
                    if 'video' in video_info and 'play_addr' in video_info['video']:
                        play_addr_list = video_info['video']['play_addr'].get('url_list', [])
                        if play_addr_list:
                            result['play_url'] = play_addr_list[0]
                    
                    return result
            
            # 如果无法提取结构化数据，尝试使用BeautifulSoup解析页面
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title = soup.select_one('title').text if soup.select_one('title') else ''
            description = soup.select_one('meta[name="description"]')
            description = description['content'] if description else ''
            
            # 尝试从页面中找到视频播放地址
            video_tag = soup.select_one('video')
            play_url = video_tag['src'] if video_tag and 'src' in video_tag.attrs else ''
            
            # 构建基本返回结果
            return {
                'title': title,
                'description': description,
                'tags': [],  # 需要更精确的解析方法提取标签
                'stats': {
                    'likes': 0,
                    'comments': 0,
                    'favorites': 0,
                    'shares': 0
                },
                'author': {
                    'name': '',
                    'id': ''
                },
                'source_url': url,
                'play_url': play_url
            }
            
        except Exception as e:
            logger.error(f"Error fetching Douyin video info: {e}")
            return None
    
    def fetch_video_info(self, platform, video_id, url):
        """根据平台获取视频信息"""
        if platform == 'douyin':
            return self.fetch_douyin_video_info(video_id, url)
        else:
            logger.info(f"Fetching for platform {platform} not yet implemented")
            return None