import os
import threading
import time
import re
from config import Config
from link_parser import LinkParser
from downloader import Downloader
from info_collector import InfoCollector
from subtitle_extractor import SubtitleExtractor
from data_exporter import DataExporter

class Controller:
    def __init__(self):
        # 初始化配置
        self.config = Config()
        
        # 初始化各模块
        self.link_parser = LinkParser()
        self.downloader = Downloader(self.config)
        self.info_collector = InfoCollector(self.downloader)
        self.subtitle_extractor = SubtitleExtractor(self.config)
        self.data_exporter = DataExporter(self.config)
        
        # 事件回调
        self.on_progress = None
        self.on_log = None
    
    def process_link(self, link, platform=None):
        """处理单个链接"""
        # 解析链接
        if platform:
            # 使用指定平台处理
            url = self._extract_url_from_text(link)
            if not url:
                return {'success': False, 'message': '未找到有效链接'}
            
            # 构造解析结果
            parse_result = {
                'success': True,
                'platform': platform,
                'url': url,
                'video_id': None  # 后续提取
            }
        else:
            # 自动识别平台
            parse_result = self.link_parser.parse_link(link)
            
            if not parse_result['success']:
                return {'success': False, 'message': parse_result.get('error', '链接解析失败')}
            
            platform = parse_result['platform']
        
        # 更新日志
        if self.on_log:
            self.on_log(f"链接已解析，平台: {platform}")
        
        # 提取视频ID
        if not parse_result.get('video_id'):
            video_id = self.link_parser.extract_video_id(parse_result['url'], platform)
            if not video_id:
                return {'success': False, 'message': '无法提取视频ID'}
            parse_result['video_id'] = video_id
        
        video_id = parse_result['video_id']
        
        # 采集视频信息
        if self.on_log:
            self.on_log(f"正在获取视频信息...")
        
        info_result = self.info_collector.collect_info(platform, video_id)
        
        if not info_result['success']:
            if info_result.get('need_login'):
                return {'success': False, 'need_login': True, 'message': '需要登录才能查看该内容'}
            return {'success': False, 'message': info_result.get('message', '获取视频信息失败')}
        
        video_info = info_result['info']
        
        # 下载视频
        if self.on_log:
            self.on_log(f"正在下载视频...")
        
        download_result = self.downloader.download_video(platform, video_id, video_info.get('title'))
        
        if not download_result['success']:
            if download_result.get('need_login'):
                return {'success': False, 'need_login': True, 'message': '需要登录才能下载该视频'}
            return {'success': False, 'message': download_result.get('message', '视频下载失败')}
        
        video_path = download_result['video_path']
        
        # 提取字幕（如果视频信息中没有文字稿）
        if not video_info.get('transcript') and os.path.exists(video_path):
            if self.on_log:
                self.on_log(f"正在提取字幕...")
            
            subtitle_result = self.subtitle_extractor.extract_from_video(video_path)
            
            if subtitle_result['success']:
                video_info['transcript'] = subtitle_result['transcript']
                if self.on_log:
                    self.on_log(f"字幕提取成功")
            else:
                if self.on_log:
                    self.on_log(f"字幕提取失败: {subtitle_result.get('message', '未知错误')}")
        
        # 导出数据到Excel
        if self.on_log:
            self.on_log(f"正在导出数据到Excel...")
        
        export_result = self.data_exporter.export_to_excel(video_info)
        
        if not export_result['success']:
            if self.on_log:
                self.on_log(f"数据导出失败: {export_result.get('message', '未知错误')}")
        else:
            if self.on_log:
                self.on_log(f"数据导出成功: {export_result.get('message', '')}")
        
        return {
            'success': True,
            'message': '视频处理完成',
            'video_path': video_path,
            'video_info': video_info
        }
    
    def process_multiple_links(self, links, platform=None):
        """处理多个链接"""
        results = []
        total = len(links)
        
        for i, link in enumerate(links):
            # 更新进度
            if self.on_progress:
                progress = (i / total) * 100
                self.on_progress(progress)
            
            # 处理单个链接
            result = self.process_link(link, platform)
            results.append(result)
        
        # 完成进度
        if self.on_progress:
            self.on_progress(100)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'success': True,
            'total': total,
            'success_count': success_count,
            'results': results
        }
    
    def _extract_url_from_text(self, text):
        """从文本中提取URL"""
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        return urls[0] if urls else None