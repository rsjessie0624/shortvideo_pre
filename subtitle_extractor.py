import os
import subprocess
import requests
import json
import base64
import time

class SubtitleExtractor:
    """从视频中提取文字内容的模块"""
    
    def __init__(self, api_key=None):
        # 如果使用百度语音识别API，需要设置API密钥
        self.api_key = api_key
        self.api_secret = None
        self.access_token = None
        
        # 尝试使用本地ffmpeg进行字幕提取
        self.use_local_ffmpeg = True
    
    def set_api_credentials(self, api_key, api_secret):
        """设置API凭证"""
        self.api_key = api_key
        self.api_secret = api_secret
    
    def extract_from_video(self, video_path):
        """从视频中提取字幕"""
        # 首先尝试从视频文件中提取内置字幕
        subtitle_text = self._extract_embedded_subtitle(video_path)
        
        # 如果没有内置字幕，尝试使用语音识别
        if not subtitle_text and self.api_key:
            subtitle_text = self._recognize_speech(video_path)
        
        return subtitle_text
    
    def _extract_embedded_subtitle(self, video_path):
        """提取视频中的内置字幕"""
        try:
            if not self.use_local_ffmpeg:
                print("未启用本地ffmpeg，跳过内置字幕提取")
                return None
            
            # 使用ffmpeg提取字幕流
            output_srt = os.path.splitext(video_path)[0] + ".srt"
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-map', '0:s:0',  # 选择第一个字幕流
                output_srt,
                '-y'  # 覆盖已存在的文件
            ]
            
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 检查是否成功提取字幕
            if os.path.exists(output_srt) and os.path.getsize(output_srt) > 0:
                # 读取SRT文件并转换为纯文本
                return self._srt_to_text(output_srt)
            
            return None
            
        except Exception as e:
            print(f"提取内置字幕时出错: {e}")
            return None
    
    def _srt_to_text(self, srt_path):
        """将SRT字幕文件转换为纯文本"""
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 删除SRT时间轴和序号，只保留文本
            lines = content.split('\n')
            text_lines = []
            
            for line in lines:
                # 跳过空行、序号行和时间轴行
                if (line.strip() and 
                    not line.strip().isdigit() and 
                    not '-->' in line):
                    text_lines.append(line.strip())
            
            # 合并文本行
            return ' '.join(text_lines)
            
        except Exception as e:
            print(f"转换SRT文件时出错: {e}")
            return None
    
    def _recognize_speech(self, video_path):
        """使用语音识别API识别视频中的语音"""
        try:
            if not self.api_key:
                print("未设置API密钥，无法进行语音识别")
                return None
            
            # 首先从视频中提取音频
            audio_path = os.path.splitext(video_path)[0] + "_temp.wav"
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # 禁用视频
                '-acodec', 'pcm_s16le',  # 设置音频编码为PCM
                '-ar', '16000',  # 设置采样率为16kHz
                '-ac', '1',  # 设置为单声道
                audio_path,
                '-y'  # 覆盖已存在的文件
            ]
            
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 获取百度AI的访问令牌
            if not self.access_token:
                self._get_baidu_token()
            
            if not self.access_token:
                print("无法获取百度AI访问令牌")
                return None
            
            # 读取音频文件
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 对音频数据进行Base64编码
            base64_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # 调用百度语音识别API
            url = "https://vop.baidu.com/server_api"
            headers = {'Content-Type': 'application/json'}
            payload = json.dumps({
                "format": "wav",
                "rate": 16000,
                "channel": 1,
                "cuid": "python_demo",
                "token": self.access_token,
                "speech": base64_audio,
                "len": len(audio_data)
            })
            
            response = requests.post(url, headers=headers, data=payload)
            result = response.json()
            
            # 清理临时音频文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # 解析识别结果
            if result.get('err_no') == 0:
                return result.get('result', [''])[0]
            else:
                print(f"语音识别失败: {result.get('err_msg')}")
                return None
            
        except Exception as e:
            print(f"语音识别过程中出错: {e}")
            return None
    
    def _get_baidu_token(self):
        """获取百度AI的访问令牌"""
        try:
            url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.api_secret}"
            response = requests.get(url)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                return True
            else:
                print(f"获取百度AI访问令牌失败: {result}")
                return False
                
        except Exception as e:
            print(f"获取百度AI访问令牌时出错: {e}")
            return False