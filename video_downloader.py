import os
import requests
from tqdm import tqdm
import subprocess

class VideoDownloader:
    """下载视频和音频内容的模块"""
    
    def __init__(self, network_request):
        self.network_request = network_request
        self.output_dir = "downloaded_videos"
        self.ensure_directory()
    
    def ensure_directory(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def sanitize_filename(self, filename):
        """清理文件名，移除不合法字符"""
        # 替换Windows和Unix系统中不允许用作文件名的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 截断过长的文件名
        if len(filename) > 50:
            filename = filename[:47] + "..."
        
        return filename
    
    def download_file(self, url, output_path, desc="Downloading"):
        """下载文件到指定路径，带进度条"""
        try:
            response = self.network_request.request(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=desc,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # 过滤掉keep-alive新块
                        f.write(chunk)
                        bar.update(len(chunk))
            
            return True
        except Exception as e:
            print(f"下载文件时出错: {e}")
            # 如果文件下载失败，删除可能部分下载的文件
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
    
    def download_douyin_video(self, video_info):
        """下载抖音视频"""
        try:
            title = video_info.get('title', 'untitled')
            video_url = video_info.get('video_url')
            
            if not video_url:
                print("没有找到视频URL")
                return None, None
            
            # 清理文件名
            safe_title = self.sanitize_filename(title)
            
            # 设置输出路径
            video_path = os.path.join(self.output_dir, f"{safe_title}.mp4")
            
            # 下载视频
            print(f"开始下载视频: {title}")
            success = self.download_file(video_url, video_path, desc=f"下载视频 '{safe_title}'")
            
            if not success:
                return None, None
            
            # 提取音频
            audio_path = os.path.join(self.output_dir, f"{safe_title}.mp3")
            print(f"正在提取音频...")
            
            try:
                # 使用ffmpeg提取音频
                command = [
                    'ffmpeg',
                    '-i', video_path,
                    '-q:a', '0',
                    '-map', 'a',
                    audio_path,
                    '-y'  # 覆盖已存在的文件
                ]
                
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"音频提取完成: {audio_path}")
            except Exception as e:
                print(f"提取音频时出错: {e}")
                audio_path = None
            
            return video_path, audio_path
            
        except Exception as e:
            print(f"下载抖音视频时出错: {e}")
            return None, None