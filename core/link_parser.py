import re
import requests
from urllib.parse import urlparse, parse_qs
from utils.common import logger, extract_url

class LinkParser:
    def __init__(self):
        self.platforms = {
            'douyin': {
                'domains': ['douyin.com', 'iesdouyin.com'],
                'patterns': [r'https?://(?:www\.)?(?:v\.)?douyin\.com/\w+/?']
            },
            'xiaohongshu': {
                'domains': ['xiaohongshu.com', 'xhslink.com'],
                'patterns': [r'https?://(?:www\.)?xiaohongshu\.com/\w+/?']
            },
            'kuaishou': {
                'domains': ['kuaishou.com', 'gifshow.com'],
                'patterns': [r'https?://(?:www\.)?kuaishou\.com/\w+/?']
            },
            'weixin': {
                'domains': ['weixin.qq.com', 'wx.qq.com'],
                'patterns': [r'https?://(?:www\.)?weixin\.qq\.com/\w+/?']
            }
        }
    
    def identify_platform(self, url):
        """识别URL所属平台"""
        if not url:
            return None
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        for platform, config in self.platforms.items():
            if any(d in domain for d in config['domains']):
                return platform
            
            for pattern in config['patterns']:
                if re.match(pattern, url):
                    return platform
        
        return None
    
    def extract_url_from_text(self, text):
        """从分享文本中提取URL"""
        return extract_url(text)
    
    def follow_redirect(self, short_url):
        """跟随短链接重定向到真实URL"""
        try:
            response = requests.head(short_url, allow_redirects=True, timeout=10)
            return response.url
        except Exception as e:
            logger.error(f"Error following redirect: {e}")
            return short_url
    
    def parse_douyin_link(self, url):
        """解析抖音链接，提取视频ID"""
        # 如果是短链接，先跟随重定向
        if '/v.douyin.com/' in url or '/www.iesdouyin.com/' in url:
            url = self.follow_redirect(url)
        
        # 提取视频ID
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # 从路径中提取视频ID
            video_id = None
            if '/video/' in path:
                video_id = path.split('/video/')[1].split('/')[0]
            
            # 从查询参数中尝试提取
            if not video_id:
                query_params = parse_qs(parsed_url.query)
                if 'item_id' in query_params:
                    video_id = query_params['item_id'][0]
            
            return {
                'platform': 'douyin',
                'video_id': video_id,
                'original_url': url
            }
        except Exception as e:
            logger.error(f"Error parsing Douyin link: {e}")
            return None
    
    def parse_link(self, input_text):
        """解析输入文本，提取链接信息"""
        # 从输入文本中提取URL
        url = self.extract_url_from_text(input_text)
        if not url:
            logger.warning(f"No URL found in input: {input_text}")
            return None
        
        # 识别平台
        platform = self.identify_platform(url)
        if not platform:
            logger.warning(f"Unknown platform for URL: {url}")
            return None
        
        # 根据平台调用相应的解析函数
        if platform == 'douyin':
            return self.parse_douyin_link(url)
        else:
            logger.info(f"Platform {platform} parsing not yet implemented")
            return {
                'platform': platform,
                'video_id': None,
                'original_url': url
            }