import os
import sys
import logging
from link_parser import LinkParser
from network_request import NetworkRequest
from video_downloader import VideoDownloader
from info_collector import InfoCollector
from subtitle_extractor import SubtitleExtractor
from data_exporter import DataExporter
from gui import VideoCollectorGUI

class VideoCollectorController:
    """主控制模块，协调各个模块工作"""
    
    def __init__(self):
        # 初始化各个模块
        self.link_parser = LinkParser()
        self.network_request = NetworkRequest()
        self.video_downloader = VideoDownloader(self.network_request)
        self.info_collector = InfoCollector(self.network_request)
        self.subtitle_extractor = SubtitleExtractor()
        self.data_exporter = DataExporter()
        
        # 尝试加载保存的cookies
        self.network_request.load_cookies()
        
        # 默认设置
        self.excel_path = 'video_info.xlsx'
        self.download_dir = 'downloaded_videos'
    
    def set_excel_path(self, path):
        """设置Excel文件路径"""
        self.excel_path = path
        self.data_exporter.set_excel_path(path)
    
    def set_download_dir(self, directory):
        """设置下载保存目录"""
        self.download_dir = directory
        self.video_downloader.output_dir = directory
        self.video_downloader.ensure_directory()
    
    def process_link(self, url):
        """处理短视频链接"""
        try:
            # 解析链接
            platform, video_id = self.link_parser.parse_link(url)
            
            if not platform or not video_id:
                print(f"无法解析链接: {url}")
                return False
            
            print(f"识别到平台: {platform}, 视频ID: {video_id}")
            
            # 处理不同平台的视频
            if platform == 'douyin':
                return self._process_douyin_video(video_id)
            else:
                print(f"{platform}平台暂不支持")
                return False
        
        except Exception as e:
            print(f"处理链接时出错: {e}")
            return False
    
    def _process_douyin_video(self, video_id):
        """处理抖音视频"""
        try:
            # 采集视频信息
            print("正在获取视频信息...")
            video_info = self.info_collector.collect_douyin_info(video_id)
            
            if not video_info:
                print("获取视频信息失败")
                return False
            
            # 下载视频和音频
            print("正在下载视频...")
            video_path, audio_path = self.video_downloader.download_douyin_video(video_info)
            
            if not video_path:
                print("下载视频失败")
                return False
            
            # 如果没有提取到完整的文字稿，尝试从视频中提取
            if not video_info.get('transcript') or len(video_info.get('transcript', '')) < 10:
                print("正在提取视频字幕...")
                transcript = self.subtitle_extractor.extract_from_video(video_path)
                
                if transcript:
                    video_info['transcript'] = transcript
                    print("字幕提取成功")
            
            # 导出信息到Excel
            print("正在导出信息到Excel...")
            export_success = self.data_exporter.export_to_excel(video_info, self.excel_path)
            
            if not export_success:
                print("导出到Excel失败")
                return False
            
            print(f"处理完成: {video_info.get('title')}")
            return True
            
        except Exception as e:
            print(f"处理抖音视频时出错: {e}")
            return False
    
    def login(self):
        """执行登录操作"""
        try:
            # 尝试调用网络请求模块的登录功能
            login_success = self.network_request._handle_login()
            
            if login_success:
                # 保存cookies
                self.network_request.save_cookies()
            
            return login_success
            
        except Exception as e:
            print(f"登录过程中出错: {e}")
            return False
    
    def run_gui(self):
        """运行GUI界面"""
        gui = VideoCollectorGUI(self)
        gui.run()

def main():
    """程序入口点"""
    try:
        # 初始化日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("video_collector.log", encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 创建控制器并运行GUI
        controller = VideoCollectorController()
        controller.run_gui()
        
    except Exception as e:
        print(f"程序启动时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()