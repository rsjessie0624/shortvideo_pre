import os
import requests
import subprocess
import tempfile
from utils.common import logger, clean_filename, create_directory

class Downloader:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        create_directory(download_dir)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        # 检查ffmpeg是否可用
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.ffmpeg_available = True
        except FileNotFoundError:
            logger.warning("ffmpeg not found. Audio extraction will be unavailable.")
            self.ffmpeg_available = False
    
    def download_file(self, url, save_path, chunk_size=8192):
        """下载文件到指定路径"""
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 计算下载进度
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        # 这里可以添加进度回调函数
            
            logger.info(f"Successfully downloaded: {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return None
    
    def extract_audio(self, video_path, audio_format='mp3'):
        """从视频中提取音频"""
        if not self.ffmpeg_available:
            logger.error("Cannot extract audio: ffmpeg not available")
            return None
        
        try:
            audio_path = os.path.splitext(video_path)[0] + f".{audio_format}"
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-q:a', '0',  # 最高音质
                '-map', 'a',   # 只提取音频
                '-y',          # 覆盖已存在的文件
                audio_path
            ]
            
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {process.stderr.decode()}")
                return None
            
            logger.info(f"Successfully extracted audio: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    
    def download_video(self, video_info, extract_audio=True):
        """下载视频并可选提取音频"""
        if not video_info or 'play_url' not in video_info or not video_info['play_url']:
            logger.error("No valid video URL provided")
            return None
        
        # 创建平台特定的下载目录
        platform_dir = os.path.join(self.download_dir, video_info.get('platform', 'unknown'))
        create_directory(platform_dir)
        
        # 生成文件名
        title = video_info.get('title', 'untitled')
        clean_title = clean_filename(title)
        video_filename = f"{clean_title}.mp4"
        video_path = os.path.join(platform_dir, video_filename)
        
        # 下载视频
        downloaded_video = self.download_file(video_info['play_url'], video_path)
        if not downloaded_video:
            return None
        
        result = {
            'video_path': downloaded_video,
            'audio_path': None
        }
        
        # 如果需要，提取音频
        if extract_audio and self.ffmpeg_available:
            result['audio_path'] = self.extract_audio(downloaded_video)
        
        return result