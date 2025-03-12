import os
import re
import logging
from datetime import datetime

# 设置日志
def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logger()

# 创建保存目录
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    return directory

# 清理文件名，移除不允许的字符
def clean_filename(filename, max_length=50):
    # 移除不合法的文件名字符
    clean_name = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 截断过长的文件名
    if len(clean_name) > max_length:
        clean_name = clean_name[:max_length]
    return clean_name.strip()

# 从文本中提取URL
def extract_url(text):
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None