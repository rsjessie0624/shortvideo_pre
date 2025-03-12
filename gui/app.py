import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import time
from utils.common import logger, create_directory
from core.link_parser import LinkParser
from core.content_fetcher import ContentFetcher
from core.downloader import Downloader
from core.subtitle import SubtitleExtractor
from core.data_processor import DataProcessor
from core.excel_exporter import ExcelExporter
from auth.login import LoginManager

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("短视频内容采集系统")
        self.root.geometry("800x600")
        
        # 初始化各模块
        self.link_parser = LinkParser()
        self.content_fetcher = ContentFetcher()
        self.downloader = Downloader()
        self.subtitle_extractor = SubtitleExtractor()
        self.data_processor = DataProcessor()
        self.excel_exporter = ExcelExporter()
        self.login_manager = LoginManager()
        
        # 设置默认下载目录
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "video_crawler")
        create_directory(self.download_dir)
        self.downloader.download_dir = self.download_dir
        
        # 设置默认Excel文件路径
        self.excel_path = os.path.join(self.download_dir, "video_data.xlsx")
        self.excel_exporter.set_excel_path(self.excel_path)
        
        # 创建UI组件
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签框架
        input_frame = ttk.LabelFrame(main_frame, text="输入链接", padding="5")
        input_frame.pack(fill=tk.X, pady=5)
        
        # 链接输入区域
        ttk.Label(input_frame, text="请输入视频链接:").pack(anchor=tk.W)
        self.link_text = scrolledtext.ScrolledText(input_frame, height=5)
        self.link_text.pack(fill=tk.X, pady=5)
        self.link_text.insert(tk.END, "粘贴链接，每行一个...")
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="下载视频", command=self.start_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="选择下载目录", command=self.select_download_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="选择Excel文件", command=self.select_excel_file).pack(side=tk.LEFT, padx=5)
        
        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 提取音频选项
        self.extract_audio_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="提取音频", variable=self.extract_audio_var).pack(anchor=tk.W)
        
        # 显示路径
        path_frame = ttk.Frame(settings_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="下载目录:").grid(row=0, column=0, sticky=tk.W)
        self.download_dir_label = ttk.Label(path_frame, text=self.download_dir)
        self.download_dir_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(path_frame, text="Excel文件:").grid(row=1, column=0, sticky=tk.W)
        self.excel_path_label = ttk.Label(path_frame, text=self.excel_path)
        self.excel_path_label.grid(row=1, column=1, sticky=tk.W)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
    
    def log(self, message):
        """添加日志到日志区域"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logger.info(message)
    
    def update_status(self, message):
        """更新状态栏信息"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def select_download_dir(self):
        """选择下载目录"""
        directory = filedialog.askdirectory(initialdir=self.download_dir)
        if directory:
            self.download_dir = directory
            self.downloader.download_dir = directory
            self.download_dir_label.config(text=directory)
            
            # 更新默认Excel路径
            self.excel_path = os.path.join(directory, "video_data.xlsx")
            self.excel_exporter.set_excel_path(self.excel_path)
            self.excel_path_label.config(text=self.excel_path)
            
            self.log(f"下载目录已设置为: {directory}")
    
    def select_excel_file(self):
        """选择Excel文件"""
        file_path = filedialog.asksaveasfilename(
            initialdir=self.download_dir,
            initialfile="video_data.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if file_path:
            self.excel_path = file_path
            self.excel_exporter.set_excel_path(file_path)
            self.excel_path_label.config(text=file_path)
            self.log(f"Excel文件已设置为: {file_path}")
    
    def process_link(self, link_text):
        """处理单个链接"""
        try:
            # 解析链接
            self.update_status("正在解析链接...")
            link_info = self.link_parser.parse_link(link_text)
            if not link_info:
                self.log(f"无法解析链接: {link_text}")
                return None
            
            platform = link_info.get('platform')
            video_id = link_info.get('video_id')
            original_url = link_info.get('original_url')
            
            self.log(f"解析链接成功: 平台={platform}, 视频ID={video_id}")
            
            # 获取视频信息
            self.update_status("正在获取视频信息...")
            video_info = self.content_fetcher.fetch_video_info(platform, video_id, original_url)
            
            # 检查是否需要登录
            if video_info and video_info.get('login_required'):
                self.log("需要登录才能获取此视频信息")
                # 弹窗提示登录
                if messagebox.askyesno("登录提示", "需要登录才能继续。是否要登录？"):
                    self.show_login_dialog(platform)
                    # 登录后重新获取视频信息
                    cookies = self.login_manager.load_cookies(platform)
                    if cookies:
                        self.content_fetcher.update_cookies(cookies)
                        video_info = self.content_fetcher.fetch_video_info(platform, video_id, original_url)
                    else:
                        self.log("登录失败或取消")
                        return None
                else:
                    return None
            
            if not video_info or not video_info.get('play_url'):
                self.log(f"无法获取视频信息或播放地址")
                return None
            
            # 下载视频
            self.update_status("正在下载视频...")
            extract_audio = self.extract_audio_var.get()
            download_info = self.downloader.download_video(video_info, extract_audio)
            
            if not download_info:
                self.log("视频下载失败")
                return None
            
            self.log(f"视频下载成功: {download_info['video_path']}")
            
            # 提取字幕
            self.update_status("正在提取字幕...")
            subtitle_text = None
            if download_info.get('video_path'):
                subtitle_text = self.subtitle_extractor.get_subtitle(
                    download_info['video_path'],
                    download_info.get('audio_path')
                )
                if subtitle_text:
                    self.log("字幕提取成功")
                else:
                    self.log("无法提取字幕")
            
            # 处理数据
            processed_data = self.data_processor.process_video_data(
                video_info,
                download_info,
                subtitle_text
            )
            
            if not processed_data:
                self.log("数据处理失败")
                return None
            
            # 导出到Excel
            self.update_status("正在导出到Excel...")
            if self.excel_exporter.export_single_item(processed_data):
                self.log(f"数据已导出到Excel: {self.excel_path}")
            else:
                self.log("数据导出失败")
            
            return processed_data
        
        except Exception as e:
            self.log(f"处理链接时出错: {str(e)}")
            logger.exception("处理链接异常")
            return None
    
    def start_download(self):
        """开始下载处理"""
        links_text = self.link_text.get("1.0", tk.END).strip()
        if not links_text or links_text == "粘贴链接，每行一个...":
            messagebox.showinfo("提示", "请输入视频链接")
            return
        
        # 分割多行链接
        links = [link.strip() for link in links_text.split('\n') if link.strip()]
        
        if not links:
            messagebox.showinfo("提示", "未找到有效链接")
            return
        
        # 禁用按钮，防止重复点击
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.DISABLED)
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 设置进度条
        self.progress['maximum'] = len(links)
        self.progress['value'] = 0
        
        # 在新线程中处理下载，避免界面卡顿
        threading.Thread(target=self.download_thread, args=(links,), daemon=True).start()
    
    def download_thread(self, links):
        """在线程中处理下载"""
        try:
            processed_count = 0
            success_count = 0
            
            for i, link in enumerate(links):
                self.log(f"处理链接 {i+1}/{len(links)}: {link}")
                
                result = self.process_link(link)
                processed_count += 1
                
                if result:
                    success_count += 1
                
                # 更新进度条
                self.progress['value'] = processed_count
                self.root.update_idletasks()
            
            # 完成处理
            self.update_status(f"处理完成: {success_count}/{len(links)} 成功")
            messagebox.showinfo("完成", f"处理完成: {success_count}/{len(links)} 成功")
        
        except Exception as e:
            self.log(f"下载过程中出错: {str(e)}")
            logger.exception("下载线程异常")
            messagebox.showerror("错误", f"处理过程中出错: {str(e)}")
        
        finally:
            # 重新启用按钮
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.NORMAL)
    
    def show_login_dialog(self, platform):
        """显示登录对话框"""
        login_window = tk.Toplevel(self.root)
        login_window.title(f"{platform} 登录")
        login_window.geometry("400x500")
        login_window.transient(self.root)  # 设置为模态窗口
        
        # 生成二维码
        qr_info = self.login_manager.generate_qr_login(platform)
        if not qr_info:
            messagebox.showerror("错误", f"无法生成{platform}登录二维码")
            login_window.destroy()
            return
        
        # 显示说明
        ttk.Label(login_window, text=f"请使用{platform}扫描二维码登录", font=("", 12)).pack(pady=10)
        
        # 显示二维码图片
        try:
            from PIL import Image, ImageTk
            qr_img = Image.open(qr_info['qr_path'])
            qr_photo = ImageTk.PhotoImage(qr_img)
            
            qr_label = ttk.Label(login_window, image=qr_photo)
            qr_label.image = qr_photo  # 保持引用，防止被回收
            qr_label.pack(pady=20)
        except Exception as e:
            ttk.Label(login_window, text=f"无法显示二维码图片: {str(e)}").pack(pady=20)
            ttk.Label(login_window, text=f"二维码保存在: {qr_info['qr_path']}").pack()
        
        # 状态显示
        status_var = tk.StringVar(value="等待扫码登录...")
        status_label = ttk.Label(login_window, textvariable=status_var)
        status_label.pack(pady=10)
        
        # 检查登录状态的线程
        def check_login_thread():
            for i in range(60):  # 最多等待60秒
                result = self.login_manager.check_login_status(platform, qr_info['qr_content'])
                if result['success']:
                    status_var.set("登录成功！")
                    # 更新cookies
                    if result['cookies']:
                        self.content_fetcher.update_cookies(result['cookies'])
                    
                    # 3秒后关闭窗口
                    login_window.after(3000, login_window.destroy)
                    return
                
                # 更新状态
                seconds_left = 60 - i
                status_var.set(f"等待扫码登录... ({seconds_left}秒)")
                
                # 暂停1秒
                time.sleep(1)
            
            # 超时处理
            status_var.set("登录超时，请重试")
            login_window.after(3000, login_window.destroy)
        
        # 启动检查线程
        threading.Thread(target=check_login_thread, daemon=True).start()
        
        # 取消按钮
        ttk.Button(login_window, text="取消", command=login_window.destroy).pack(pady=10)