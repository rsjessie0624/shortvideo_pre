import sys
import os
import time
from controller import Controller
from gui import VideoCollectorGUI

def main():
    # 创建控制器
    controller = Controller()
    
    # 创建GUI
    gui = VideoCollectorGUI(controller)
    
    # 运行GUI
    gui.run()

if __name__ == "__main__":
    main()