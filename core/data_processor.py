import os
from utils.common import logger

class DataProcessor:
    def __init__(self):
        pass
    
    def process_video_data(self, video_info, download_info, subtitle_text):
        """
        处理视频数据，整合所有相关信息
        
        Args:
            video_info: 从平台获取的视频信息
            download_info: 下载结果信息
            subtitle_text: 提取的字幕文本
        
        Returns:
            处理后的完整数据字典
        """
        if not video_info:
            logger.error("No video information provided")
            return None
        
        # 合并数据
        processed_data = {
            'title': video_info.get('title', ''),
            'description': video_info.get('description', ''),
            'tags': ', '.join(video_info.get('tags', [])),
            'transcript': subtitle_text or '',
            'likes': video_info.get('stats', {}).get('likes', 0),
            'comments': video_info.get('stats', {}).get('comments', 0),
            'favorites': video_info.get('stats', {}).get('favorites', 0),
            'shares': video_info.get('stats', {}).get('shares', 0),
            'author_name': video_info.get('author', {}).get('name', ''),
            'author_id': video_info.get('author', {}).get('id', ''),
            'source_url': video_info.get('source_url', ''),
            'platform': video_info.get('platform', 'unknown'),
            'video_id': video_info.get('video_id', ''),
            'local_video_path': download_info.get('video_path', '') if download_info else '',
            'local_audio_path': download_info.get('audio_path', '') if download_info else ''
        }
        
        return processed_data
    
    def batch_process(self, data_items):
        """
        批量处理多个视频数据项
        
        Args:
            data_items: 多个视频数据项的列表
        
        Returns:
            处理后的数据项列表
        """
        processed_items = []
        for item in data_items:
            video_info = item.get('video_info')
            download_info = item.get('download_info')
            subtitle_text = item.get('subtitle_text')
            
            processed_item = self.process_video_data(video_info, download_info, subtitle_text)
            if processed_item:
                processed_items.append(processed_item)
        
        return processed_items