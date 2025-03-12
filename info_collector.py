import json
import re

class InfoCollector:
    """采集视频相关信息的模块"""
    
    def __init__(self, network_request):
        self.network_request = network_request
    
    def collect_douyin_info(self, video_id):
        """采集抖音视频信息"""
        try:
            # 获取视频详情API (这需要根据抖音实际API调整)
            api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
            
            response = self.network_request.request(api_url)
            
            if not response or response.status_code != 200:
                print(f"获取视频信息失败: HTTP {response.status_code if response else 'No response'}")
                return None
            
            data = response.json()
            
            # 提取所需信息
            aweme_detail = data.get('aweme_detail', {})
            
            video_info = {
                "title": aweme_detail.get('desc', '无标题'),
                "description": aweme_detail.get('desc', ''),
                "tags": self._extract_tags(aweme_detail.get('desc', '')),
                "transcript": self._extract_transcript(aweme_detail),
                "stats": {
                    "likes": aweme_detail.get('statistics', {}).get('digg_count', 0),
                    "comments": aweme_detail.get('statistics', {}).get('comment_count', 0),
                    "favorites": aweme_detail.get('statistics', {}).get('collect_count', 0),
                    "shares": aweme_detail.get('statistics', {}).get('share_count', 0)
                },
                "author": {
                    "name": aweme_detail.get('author', {}).get('nickname', '未知用户'),
                    "id": aweme_detail.get('author', {}).get('unique_id', '')
                },
                "source_url": f"https://www.douyin.com/video/{video_id}",
                "video_url": self._extract_video_url(aweme_detail)
            }
            
            return video_info
            
        except Exception as e:
            print(f"采集抖音视频信息时出错: {e}")
            return None
    
    def _extract_tags(self, description):
        """从描述中提取标签"""
        # 抖音标签通常是 #标签内容 的形式
        tags = re.findall(r'#(\w+)', description)
        return tags
    
    def _extract_transcript(self, aweme_detail):
        """提取视频文字内容"""
        # 如果有字幕，从字幕中提取
        captions = aweme_detail.get('captions', [])
        if captions:
            return ' '.join([caption.get('text', '') for caption in captions])
        
        # 否则返回视频描述
        return aweme_detail.get('desc', '')
    
    def _extract_video_url(self, aweme_detail):
        """提取视频URL"""
        # 尝试获取无水印视频链接
        try:
            video_info = aweme_detail.get('video', {})
            play_addr = video_info.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            
            # 优先选择高清无水印链接
            for url in url_list:
                if 'play_addr' in url and 'playwm' not in url:
                    return url
            
            # 如果没有找到高清无水印链接，返回第一个可用链接
            if url_list:
                return url_list[0]
            
        except Exception as e:
            print(f"提取视频URL时出错: {e}")
        
        return None