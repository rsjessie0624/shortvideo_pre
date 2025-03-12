import requests
import time
import random
import json
import qrcode
from PIL import Image
import os

class NetworkRequest:
    """处理网络请求的模块，包括反爬处理"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.cookies = {}
    
    def request(self, url, method='GET', params=None, data=None, json_data=None, retry=3):
        """发送HTTP请求，支持重试"""
        for attempt in range(retry):
            try:
                # 随机延迟，避免频繁请求
                time.sleep(random.uniform(1, 3))
                
                if method.upper() == 'GET':
                    response = self.session.get(
                        url, 
                        params=params, 
                        timeout=10
                    )
                elif method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        params=params, 
                        data=data, 
                        json=json_data, 
                        timeout=10
                    )
                else:
                    raise ValueError(f"不支持的请求方法: {method}")
                
                # 检查是否需要登录
                if self._needs_login(response):
                    self._handle_login()
                    continue
                
                return response
            
            except Exception as e:
                print(f"请求出错 (尝试 {attempt+1}/{retry}): {e}")
                if attempt == retry - 1:
                    raise
        
        return None
    
    def _needs_login(self, response):
        """检查是否需要登录"""
        # 这里的判断逻辑需要根据抖音的实际响应来调整
        if response.status_code == 403:
            return True
        
        try:
            response_json = response.json()
            if response_json.get('status_code') == 2154 or 'login' in response_json.get('message', '').lower():
                return True
        except:
            pass
        
        return False
    
    def _handle_login(self):
        """处理登录流程"""
        print("检测到需要登录，正在生成二维码...")
        
        try:
            # 获取二维码登录URL (这部分需要根据抖音实际的登录API调整)
            qr_response = self.session.get('https://sso.douyin.com/get_qrcode/')
            qr_data = qr_response.json()
            
            if qr_data.get('status_code') == 0:
                qr_url = qr_data.get('data', {}).get('qrcode_url')
                token = qr_data.get('data', {}).get('token')
                
                # 生成二维码图片
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                img.save('douyin_login_qr.png')
                
                # 显示二维码
                Image.open('douyin_login_qr.png').show()
                
                print("请使用抖音APP扫描二维码登录")
                
                # 循环检查登录状态
                for _ in range(60):  # 最多等待60秒
                    time.sleep(1)
                    check_response = self.session.get(
                        f'https://sso.douyin.com/check_qrcode/?token={token}'
                    )
                    check_data = check_response.json()
                    
                    if check_data.get('status_code') == 0 and check_data.get('data', {}).get('status') == 'confirmed':
                        print("登录成功!")
                        # 更新cookies
                        self.cookies.update(self.session.cookies.get_dict())
                        return True
                
                print("登录超时，请重试")
                return False
            
            else:
                print("获取二维码失败")
                return False
                
        except Exception as e:
            print(f"登录过程中出错: {e}")
            return False
    
    def save_cookies(self, filepath='cookies.json'):
        """保存cookies到文件"""
        with open(filepath, 'w') as f:
            json.dump(dict(self.session.cookies), f)
    
    def load_cookies(self, filepath='cookies.json'):
        """从文件加载cookies"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
                return True
        return False