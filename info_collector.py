import re
import json
import time
import requests
from utils import format_number

class InfoCollector:
    def __init__(self, downloader):
        self.downloader = downloader
        self.session = downloader.session
    
    def collect_douyin_info(self, video_id):
        """采集抖音视频信息"""
        # 构建API请求URL
        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}"
        
        try:
            # 获取视频信息
            response = self.session.get(api_url, timeout=30)
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
            
            # 解析数据
            info = {
                'title': item.get('desc', ''),
                'description': item.get('desc', ''),
                'tags': [],
                'transcript': '',
                'stats': {
                    'likes': format_number(item.get('statistics', {}).get('digg_count', 0)),
                    'comments': format_number(item.get('statistics', {}).get('comment_count', 0)),
                    'favorites': format_number(item.get('statistics', {}).get('collect_count', 0)),
                    'shares': format_number(item.get('statistics', {}).get('share_count', 0))
                },
                'author': {
                    'name': item.get('author', {}).get('nickname', ''),
                    'id': item.get('author', {}).get('unique_id', '')
                },
                'source_url': f"https://www.douyin.com/video/{video_id}"
            }
            
            # 提取标签
            text_extra = item.get('text_extra', [])
            for text in text_extra:
                if 'hashtag_name' in text and text['hashtag_name']:
                    info['tags'].append(text['hashtag_name'])
            
            # 尝试获取文字稿
            self._get_douyin_transcript(video_id, info)
            
            return {'success': True, 'info': info}
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'网络请求异常: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'获取抖音视频信息失败: {str(e)}'}
    
    def _get_douyin_transcript(self, video_id, info):
        """获取抖音视频文字稿"""
        # 尝试通过额外API获取文字稿
        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={video_id}&subtitle=1"
        
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            item_list = data.get('item_list', [])
            
            if item_list:
                item = item_list[0]
                # 获取字幕信息
                video_captions = item.get('video_captions', [])
                
                if video_captions:
                    # 合并所有字幕文本
                    transcript = ""
                    for caption in video_captions:
                        caption_list = caption.get('caption_list', [])
                        for cap in caption_list:
                            if 'text' in cap:
                                transcript += cap['text'] + " "
                    
                    info['transcript'] = transcript.strip()
        except Exception as e:
            print(f"获取抖音文字稿失败: {e}")
    
    def collect_info(self, platform, video_id):
        """根据平台采集视频信息"""
        if platform == 'douyin':
            return self.collect_douyin_info(video_id)
        elif platform == 'xiaohongshu':
            return {'success': False, 'message': '小红书视频信息采集功能开发中'}
        elif platform == 'kuaishou':
            return {'success': False, 'message': '快手视频信息采集功能开发中'}
        elif platform == 'weixin':
            return {'success': False, 'message': '微信视频号信息采集功能开发中'}
        else:
            return {'success': False, 'message': '不支持的平台'}