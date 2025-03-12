import os
import json
import re
import requests
import subprocess
import time
import base64
import hashlib
import hmac

class SubtitleExtractor:
    def __init__(self, config):
        self.config = config
        # 百度API配置
        self.baidu_api = {
            'enable': False,
            'app_id': '',
            'api_key': '',
            'secret_key': ''
        }
        
        # 讯飞API配置
        self.xunfei_api = {
            'enable': False,
            'app_id': '',
            'api_key': '',
            'api_secret': ''
        }
        
        # 加载API配置
        self._load_api_config()
    
    def _load_api_config(self):
        """加载API配置"""
        api_config_file = os.path.join(self.config.config_dir, 'api_config.json')
        if os.path.exists(api_config_file):
            try:
                with open(api_config_file, 'r', encoding='utf-8') as f:
                    api_config = json.load(f)
                
                # 更新百度API配置
                if 'baidu_api' in api_config:
                    self.baidu_api.update(api_config['baidu_api'])
                
                # 更新讯飞API配置
                if 'xunfei_api' in api_config:
                    self.xunfei_api.update(api_config['xunfei_api'])
                    
                print("已加载API配置")
            except Exception as e:
                print(f"加载API配置失败: {e}")
    
    def save_api_config(self):
        """保存API配置"""
        api_config = {
            'baidu_api': self.baidu_api,
            'xunfei_api': self.xunfei_api
        }
        
        api_config_file = os.path.join(self.config.config_dir, 'api_config.json')
        try:
            with open(api_config_file, 'w', encoding='utf-8') as f:
                json.dump(api_config, f, ensure_ascii=False, indent=4)
            print("API配置已保存")
            return True
        except Exception as e:
            print(f"保存API配置失败: {e}")
            return False
    
    def extract_from_video(self, video_path):
        """从视频中提取字幕"""
        # 检查ffmpeg是否可用
        if not self._check_ffmpeg():
            return {'success': False, 'message': '未找到ffmpeg，无法提取音频'}
        
        # 提取音频
        audio_path = video_path.replace('.mp4', '.wav')
        if not self._extract_audio(video_path, audio_path):
            return {'success': False, 'message': '提取音频失败'}
        
        # 尝试从视频中直接提取字幕
        result = self._extract_embedded_subtitle(video_path)
        if result['success']:
            # 删除临时音频文件
            try:
                os.remove(audio_path)
            except:
                pass
            return result
        
        # 优先使用百度API
        if self.baidu_api['enable'] and self.baidu_api['app_id'] and self.baidu_api['api_key'] and self.baidu_api['secret_key']:
            result = self._recognize_baidu(audio_path)
            if result['success']:
                # 删除临时音频文件
                try:
                    os.remove(audio_path)
                except:
                    pass
                return result
        
        # 尝试使用讯飞API
        if self.xunfei_api['enable'] and self.xunfei_api['app_id'] and self.xunfei_api['api_key'] and self.xunfei_api['api_secret']:
            result = self._recognize_xunfei(audio_path)
            if result['success']:
                # 删除临时音频文件
                try:
                    os.remove(audio_path)
                except:
                    pass
                return result
        
        # 删除临时音频文件
        try:
            os.remove(audio_path)
        except:
            pass
        
        return {'success': False, 'message': '无法提取字幕，请配置语音识别API或使用带字幕的视频'}
    
    def _check_ffmpeg(self):
        """检查ffmpeg是否可用"""
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except:
            return False
    
    def _extract_audio(self, video_path, audio_path):
        """从视频中提取音频"""
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '16000', '-ac', '1', audio_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return os.path.exists(audio_path)
        except Exception as e:
            print(f"提取音频失败: {e}")
            return False
    
    def _extract_embedded_subtitle(self, video_path):
        """从视频中提取嵌入的字幕"""
        try:
            # 获取字幕信息
            result = subprocess.run([
                'ffmpeg', '-i', video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            output = result.stderr
            
            # 查找字幕流
            subtitle_streams = re.findall(r'Stream #\d+:\d+(?:\(.*?\))?: Subtitle', output)
            
            if subtitle_streams:
                # 提取字幕到文件
                subtitle_path = video_path.replace('.mp4', '.srt')
                subprocess.run([
                    'ffmpeg', '-i', video_path, '-map', '0:s:0', subtitle_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if os.path.exists(subtitle_path):
                    # 读取字幕文件内容
                    with open(subtitle_path, 'r', encoding='utf-8') as f:
                        subtitle_text = f.read()
                    
                    # 解析字幕文本
                    transcript = self._parse_subtitle(subtitle_text)
                    
                    # 删除字幕文件
                    try:
                        os.remove(subtitle_path)
                    except:
                        pass
                    
                    return {'success': True, 'transcript': transcript}
            
            return {'success': False, 'message': '视频中没有嵌入字幕'}
        except Exception as e:
            print(f"提取嵌入字幕失败: {e}")
            return {'success': False, 'message': f'提取嵌入字幕失败: {str(e)}'}
    
    def _parse_subtitle(self, subtitle_text):
        """解析SRT字幕文本，提取纯文本内容"""
        # 移除时间戳和序号行
        lines = subtitle_text.split('\n')
        text_lines = []
        
        i = 0
        while i < len(lines):
            # 跳过序号行
            if lines[i].strip().isdigit():
                i += 1
                continue
            
            # 跳过时间戳行
            if '-->' in lines[i]:
                i += 1
                continue
            
            # 添加文本行
            if lines[i].strip():
                text_lines.append(lines[i].strip())
            
            i += 1
        
        # 合并文本行
        return ' '.join(text_lines)
    
    def _recognize_baidu(self, audio_path):
        """使用百度语音识别API提取文字"""
        try:
            # 获取token
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.baidu_api['api_key']}&client_secret={self.baidu_api['secret_key']}"
            response = requests.get(token_url)
            token = response.json().get('access_token')
            
            if not token:
                return {'success': False, 'message': '获取百度API Token失败'}
            
            # 读取音频文件
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 对音频数据进行base64编码
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 识别参数
            params = {
                'format': 'wav',
                'rate': 16000,
                'channel': 1,
                'cuid': self.baidu_api['app_id'],
                'token': token,
                'dev_pid': 1537,  # 普通话(支持简单的英文识别)
                'speech': audio_base64,
                'len': len(audio_data)
            }
            
            # 发送请求
            api_url = 'https://vop.baidu.com/server_api'
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, json=params, headers=headers)
            result = response.json()
            
            # 检查结果
            if result.get('err_no') == 0:
                transcript = ' '.join([res['result'][0] for res in result.get('result', [])])
                return {'success': True, 'transcript': transcript}
            else:
                return {'success': False, 'message': f"百度语音识别失败: {result.get('err_msg', '未知错误')}"}
        except Exception as e:
            print(f"百度语音识别失败: {e}")
            return {'success': False, 'message': f'百度语音识别失败: {str(e)}'}
    
    def _recognize_xunfei(self, audio_path):
        """使用讯飞语音识别API提取文字"""
        # 此处省略实现，与百度API类似
        return {'success': False, 'message': '讯飞语音识别功能开发中'}