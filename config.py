import os
import json

class Config:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".video_collector")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.cookies_dir = os.path.join(self.config_dir, "cookies")
        
        # 默认配置
        self.default_config = {
            "download_path": os.path.join(os.path.expanduser("~"), "Downloads", "video_collector"),
            "excel_path": os.path.join(os.path.expanduser("~"), "Downloads", "video_collector", "data.xlsx"),
            "auto_login": True,
            "max_retry": 3,
            "timeout": 30,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        self.config = self.default_config.copy()
        self._init_config()
        
    def _init_config(self):
        """初始化配置"""
        # 创建配置目录
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # 创建cookies目录
        if not os.path.exists(self.cookies_dir):
            os.makedirs(self.cookies_dir)
            
        # 加载配置文件
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        else:
            self.save_config()
            
        # 确保下载目录存在
        if not os.path.exists(self.config["download_path"]):
            os.makedirs(self.config["download_path"])
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()