import re
import requests

class LinkParser:
    """解析短视频平台链接的模块"""
    
    def __init__(self):
        # 各平台的链接正则表达式
        self.patterns = {
            'douyin': r'(?:https?://)?(?:www\.)?(?:v\.douyin\.com)/([a-zA-Z0-9]+)',
            'xiaohongshu': r'(?:https?://)?(?:www\.)?(?:xiaohongshu\.com)/([a-zA-Z0-9]+)',
            'shipin': r'(?:https?://)?(?:www\.)?(?:channels\.weixin\.qq\.com)/([a-zA-Z0-9]+)',
            'kuaishou': r'(?:https?://)?(?:www\.)?(?:v\.kuaishou\.com)/([a-zA-Z0-9]+)'
        }
    
    def identify_platform(self, url):
        """识别链接所属平台"""
        for platform, pattern in self.patterns.items():
            if re.search(pattern, url):
                return platform
        return None
    
    def parse_douyin_link(self, url):
        """解析抖音链接，获取视频ID"""
        try:
            # 处理抖音短链接重定向
            response = requests.head(url, allow_redirects=True)
            final_url = response.url
            
            # 从最终URL中提取视频ID
            video_id = re.search(r'/video/(\d+)', final_url)
            if video_id:
                return video_id.group(1)
            return None
        except Exception as e:
            print(f"解析抖音链接时出错: {e}")
            return None
    
    def parse_link(self, url):
        """解析链接，返回平台和视频ID"""
        platform = self.identify_platform(url)
        
        if platform is None:
            return None, None
        
        if platform == 'douyin':
            video_id = self.parse_douyin_link(url)
            return platform, video_id
        
        # 其他平台的解析方法将在后续开发中实现
        print(f"{platform}平台的解析功能尚未实现")
        return platform, None