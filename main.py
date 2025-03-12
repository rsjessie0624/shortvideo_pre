import sys
import tkinter as tk
from gui.app import VideoDownloaderApp
from utils.common import setup_logger

def main():
    # 设置日志
    logger = setup_logger()
    logger.info("Starting Video Crawler Application")
    
    # 创建Tkinter根窗口
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    
    # 启动应用
    try:
        root.mainloop()
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
    finally:
        logger.info("Application closed")

if __name__ == "__main__":
    main()