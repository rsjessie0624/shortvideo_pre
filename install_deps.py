import subprocess
import sys
import os

def install_dependencies():
    """安装所需的依赖包"""
    print("开始安装依赖...")
    
    # 依赖列表
    dependencies = [
        "requests",
        "pandas",
        "openpyxl",
        "pillow",
        "qrcode",
    ]
    
    # 安装FFMPEG
    print("请确保已安装FFMPEG，程序需要使用它来处理视频")
    print("FFMPEG下载地址: https://ffmpeg.org/download.html")
    
    # 使用pip安装依赖
    for dep in dependencies:
        print(f"正在安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"{dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"{dep} 安装失败")
            return False
    
    print("\n所有依赖安装完成！")
    return True

if __name__ == "__main__":
    install_dependencies()
    
    print("\n按回车键退出...")
    input()