import re
import requests
from urllib.parse import urlparse, parse_qs

class LinkParser:
    def __init__(self):
        # 各平台的链接正则表达式
        self.patterns = {
            'douyin': r'(?:https?://)?(?:www\.)?(?:v\.douyin\.com|douyin\.com)/(?:[^/]+/)?([^/\s?]+)',
            'xiaohongshu': r'(?:https?://)?(?:www\.)?xiaohongshu\.com/(?:discovery/item|item)/([^/\s?]+)',
            'kuaishou': r'(?:https?://)?(?:www\.)?kuaishou\.com/(?:short-video|photo)/([^/\s?]+)',
            'weishi': r'(?:https?://)?(?:www\.)?weishi\.qq\.com/(?:\w+/)?([^/\s?]+)'
        }
    
    def parse_link(self, link):
        """
        解析链接，返回平台名称和视频ID
        """
        # 清理链接，去除多余空格和换行符
        link = link.strip()
        
        # 检查是否是短链接并需要重定向
        if 'v.douyin.com' in link or any(domain in link for domain in ['t.cn', 'b23.tv', 'dwz.cn']):
            try:
                response = requests.head(link, allow_redirects=True, timeout=10)
                link = response.url
            except Exception as e:
                raise Exception(f"解析短链接失败: {str(e)}")
        
        # 识别平台
        platform = None
        video_id = None
        
        for platform_name, pattern in self.patterns.items():
            match = re.search(pattern, link)
            if match:
                platform = platform_name
                video_id = match.group(1)
                break
        
        if not platform or not video_id:
            # 如果仍然无法识别，尝试解析URL参数
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)
            
            # 针对抖音特殊处理
            if 'douyin.com' in parsed_url.netloc:
                platform = 'douyin'
                if 'video_id' in query_params:
                    video_id = query_params['video_id'][0]
                elif 'item_ids' in query_params:
                    video_id = query_params['item_ids'][0]
            
            # 如果还是没找到，可能需要登录或使用特殊方法
            if not video_id:
                raise Exception(f"无法解析链接: {link}")
        
        return {
            'platform': platform,
            'video_id': video_id,
            'original_url': link
        }
    
    def batch_parse_links(self, links):
        """
        批量解析多个链接
        """
        results = []
        errors = []
        
        for link in links:
            if not link.strip():
                continue
                
            try:
                result = self.parse_link(link)
                results.append(result)
            except Exception as e:
                errors.append({
                    'link': link,
                    'error': str(e)
                })
        
        return {
            'results': results,
            'errors': errors
        }


if __name__ == "__main__":
    # 测试代码
    parser = LinkParser()
    
    test_links = [
        "4.35 Rxf:/ H@V.YZ 09/20 主图多放一个元素 点击率暴跌70%% # 电商主图 # 电商 # 主图 # 设计  https://v.douyin.com/i5rSM7Y7/ 复制此链接，打开Dou音搜索，直接观看视频！",
    ]
    
    for link in test_links:
        try:
            result = parser.parse_link(link)
            print(f"链接: {link}")
            print(f"平台: {result['platform']}")
            print(f"视频ID: {result['video_id']}")
            print(f"原始URL: {result['original_url']}")
        except Exception as e:
            print(f"解析失败: {link}")
            print(f"错误信息: {str(e)}")