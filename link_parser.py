import re
import requests
from urllib.parse import urlparse, parse_qs
from utils import follow_redirects, extract_url_from_text

class LinkParser:
    def __init__(self):
        # 各平台匹配模式
        self.patterns = {
            'douyin': {
                'url_pattern': r'https?://(?:www\.)?(?:v\.douyin\.com|douyin\.com)/[^\s]+',
                'share_pattern': r'https?://(?:www\.)?(?:v\.douyin\.com)/[^\s]+'
            },
            'xiaohongshu': {
                'url_pattern': r'https?://(?:www\.)?(?:xiaohongshu\.com|xhslink\.com)/[^\s]+',
                'share_pattern': r'https?://(?:www\.)?(?:xhslink\.com)/[^\s]+'
            },
            'kuaishou': {
                'url_pattern': r'https?://(?:www\.)?(?:kuaishou\.com|gifshow\.com)/[^\s]+',
                'share_pattern': r'https?://(?:www\.)?(?:v\.kuaishou\.com)/[^\s]+'
            },
            'weixin': {
                'url_pattern': r'https?://(?:www\.)?(?:weixin\.qq\.com|wx\.qq\.com)/[^\s]+',
                'share_pattern': r'https?://(?:www\.)?(?:weixin\.qq\.com|wx\.qq\.com)/[^\s]+'
            }
        }
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.douyin.com/'
        }
    
    def extract_video_id(self, url, platform):
        """根据平台提取视频ID"""
        if platform == 'douyin':
            return self._extract_douyin_id(url)
        elif platform == 'xiaohongshu':
            return self._extract_xiaohongshu_id(url)
        elif platform == 'kuaishou':
            return self._extract_kuaishou_id(url)
        elif platform == 'weixin':
            return self._extract_weixin_id(url)
        else:
            return None
    
    def _extract_douyin_id(self, url):
        """提取抖音视频ID"""
        # 跟随重定向获取完整URL
        final_url = follow_redirects(url)
        
        # 方法1: 从URL路径中提取
        if '/video/' in final_url:
            video_id = final_url.split('/video/')[1].split('/')[0].split('?')[0]
            return video_id
            
        # 方法2: 从查询参数中提取
        parsed_url = urlparse(final_url)
        query_params = parse_qs(parsed_url.query)
        if 'item_ids' in query_params:
            return query_params['item_ids'][0]
        
        # 尝试访问页面提取视频ID
        try:
            response = requests.get(final_url, headers=self.headers, timeout=10)
            match = re.search(r'"aweme_id":"(\d+)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"提取抖音视频ID失败: {e}")
        
        return None
    
    def _extract_xiaohongshu_id(self, url):
        """提取小红书视频ID"""
        final_url = follow_redirects(url)
        
        # 从URL路径中提取
        if '/item/' in final_url:
            return final_url.split('/item/')[1].split('/')[0]
        
        # 尝试访问页面提取
        try:
            response = requests.get(final_url, headers=self.headers, timeout=10)
            match = re.search(r'"noteId":"([^"]+)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"提取小红书视频ID失败: {e}")
        
        return None
    
    def _extract_kuaishou_id(self, url):
        """提取快手视频ID"""
        final_url = follow_redirects(url)
        
        # 从URL路径中提取
        if '/short-video/' in final_url:
            return final_url.split('/short-video/')[1].split('/')[0]
        
        # 从查询参数中提取
        parsed_url = urlparse(final_url)
        query_params = parse_qs(parsed_url.query)
        if 'photoId' in query_params:
            return query_params['photoId'][0]
        
        # 尝试访问页面提取
        try:
            response = requests.get(final_url, headers=self.headers, timeout=10)
            match = re.search(r'"photoId":"([^"]+)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"提取快手视频ID失败: {e}")
        
        return None
    
    def _extract_weixin_id(self, url):
        """提取微信视频号视频ID"""
        final_url = follow_redirects(url)
        
        # 从查询参数中提取
        parsed_url = urlparse(final_url)
        query_params = parse_qs(parsed_url.query)
        if 'vid' in query_params:
            return query_params['vid'][0]
        
        if 'object_id' in query_params:
            return query_params['object_id'][0]
        
        # 尝试访问页面提取
        try:
            response = requests.get(final_url, headers=self.headers, timeout=10)
            match = re.search(r'"vid":"([^"]+)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"提取微信视频号视频ID失败: {e}")
        
        return None
    
    def parse_link(self, input_text):
        """解析输入文本，提取视频链接和平台信息"""
        result = {'success': False, 'platform': None, 'video_id': None, 'url': None}
        
        # 提取URL
        url = extract_url_from_text(input_text)
        if not url:
            result['error'] = "未找到有效链接"
            return result
            
        result['url'] = url
        
        # 判断平台
        for platform, patterns in self.patterns.items():
            if re.search(patterns['url_pattern'], url) or re.search(patterns['share_pattern'], url):
                result['platform'] = platform
                break
        
        if not result['platform']:
            result['error'] = "不支持的平台链接"
            return result
        
        # 提取视频ID
        video_id = self.extract_video_id(url, result['platform'])
        if not video_id:
            result['error'] = "无法提取视频ID"
            return result
            
        result['video_id'] = video_id
        result['success'] = True
        return result