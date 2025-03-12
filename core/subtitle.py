import os
import subprocess
import tempfile
from utils.common import logger

class SubtitleExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        # 检查ffmpeg是否可用
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.ffmpeg_available = True
        except FileNotFoundError:
            logger.warning("ffmpeg not found. Some subtitle extraction features may be unavailable.")
            self.ffmpeg_available = False
    
    def extract_embedded_subtitle(self, video_path):
        """提取视频中嵌入的字幕"""
        if not self.ffmpeg_available:
            logger.error("Cannot extract subtitle: ffmpeg not available")
            return None
        
        try:
            subtitle_path = os.path.splitext(video_path)[0] + ".srt"
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-map', '0:s:0',  # 选择第一个字幕流
                '-y',              # 覆盖已存在的文件
                subtitle_path
            ]
            
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 检查字幕文件是否生成
            if os.path.exists(subtitle_path) and os.path.getsize(subtitle_path) > 0:
                logger.info(f"Successfully extracted subtitle: {subtitle_path}")
                return subtitle_path
            else:
                logger.warning("No embedded subtitle found in video")
                return None
        except Exception as e:
            logger.error(f"Error extracting embedded subtitle: {e}")
            return None
    
    def extract_audio_to_text(self, audio_path):
        """
        使用语音识别API将音频转换为文本
        注意：这需要外部API支持，这里只是一个占位实现
        """
        logger.info("Audio to text conversion requires an external API")
        logger.info("Please implement integration with a speech recognition service")
        
        # 实际实现需要调用语音识别API
        # 例如百度AI、讯飞等
        
        return "This is a placeholder for speech recognition result."
    
    def get_subtitle(self, video_path, audio_path=None):
        """
        尝试获取字幕，优先从视频中提取，如果没有则尝试语音识别
        """
        # 先尝试提取嵌入字幕
        subtitle_path = self.extract_embedded_subtitle(video_path)
        if subtitle_path:
            # 读取字幕文件并返回纯文本
            try:
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 移除时间戳和序号，保留文本
                import re
                text_only = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
                text_only = re.sub(r'\n\n+', '\n', text_only).strip()
                return text_only
            except Exception as e:
                logger.error(f"Error reading subtitle file: {e}")
        
        # 如果没有嵌入字幕且提供了音频路径，尝试语音识别
        if audio_path:
            return self.extract_audio_to_text(audio_path)
        
        return None