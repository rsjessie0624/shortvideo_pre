import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys

class VideoCollectorGUI:
    """简洁的GUI界面"""
    
    def __init__(self, controller):
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """初始化GUI界面"""
        self.root = tk.Tk()
        self.root.title("短视频内容采集系统")
        self.root.geometry("600x400")
        self.root.minsize(600, 400)
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 链接输入框
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(link_frame, text="视频链接:").pack(side=tk.LEFT)
        self.link_entry = ttk.Entry(link_frame, width=50)
        self.link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 下载按钮
        self.download_button = ttk.Button(
            link_frame, 
            text="下载", 
            command=self.start_download
        )
        self.download_button.pack(side=tk.RIGHT)
        
        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Excel路径设置
        excel_frame = ttk.Frame(settings_frame)
        excel_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(excel_frame, text="Excel保存路径:").pack(side=tk.LEFT)
        self.excel_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "video_info.xlsx"))
        excel_path_entry = ttk.Entry(excel_frame, textvariable=self.excel_path_var, width=40)
        excel_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        excel_browse_button = ttk.Button(
            excel_frame, 
            text="浏览...", 
            command=self.browse_excel_path
        )
        excel_browse_button.pack(side=tk.RIGHT)
        
        # 下载目录设置
        download_dir_frame = ttk.Frame(settings_frame)
        download_dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(download_dir_frame, text="下载保存目录:").pack(side=tk.LEFT)
        self.download_dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "downloaded_videos"))
        download_dir_entry = ttk.Entry(download_dir_frame, textvariable=self.download_dir_var, width=40)
        download_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        download_dir_button = ttk.Button(
            download_dir_frame, 
            text="浏览...", 
            command=self.browse_download_dir
        )
        download_dir_button.pack(side=tk.RIGHT)
        
        # 状态和日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 添加日志文本框和滚动条
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, yscrollcommand=log_scroll.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT)
        
        # 底部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.login_button = ttk.Button(
            button_frame, 
            text="登录", 
            command=self.login
        )
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        exit_button = ttk.Button(
            button_frame, 
            text="退出", 
            command=self.root.destroy
        )
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # 初始化日志重定向
        self._redirect_stdout()
    
    def _redirect_stdout(self):
        """重定向标准输出到GUI日志文本框"""
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget
            
            def write(self, string):
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
            
            def flush(self):
                pass
        
        sys.stdout = StdoutRedirector(self.log_text)
    
    def browse_excel_path(self):
        """浏览并选择Excel保存路径"""
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialdir=os.path.dirname(self.excel_path_var.get()),
            initialfile=os.path.basename(self.excel_path_var.get())
        )
        if path:
            self.excel_path_var.set(path)
            self.controller.set_excel_path(path)
    
    def browse_download_dir(self):
        """浏览并选择下载保存目录"""
        directory = filedialog.askdirectory(
            initialdir=self.download_dir_var.get()
        )
        if directory:
            self.download_dir_var.set(directory)
            self.controller.set_download_dir(directory)
    
    def start_download(self):
        """开始下载视频"""
        link = self.link_entry.get().strip()
        
        if not link:
            messagebox.showerror("错误", "请输入视频链接")
            return
        
        # 禁用下载按钮，避免重复点击
        self.download_button.config(state=tk.DISABLED)
        self.status_var.set("正在下载...")
        self.progress_var.set(0)
        
        # 在新线程中执行下载，避免界面卡顿
        threading.Thread(target=self._download_thread, args=(link,), daemon=True).start()
    
    def _download_thread(self, link):
        """下载线程"""
        try:
            # 调用控制器执行下载
            result = self.controller.process_link(link)
            
            # 在主线程中更新UI
            self.root.after(0, self._update_ui_after_download, result)
            
        except Exception as e:
            print(f"下载过程中出错: {e}")
            # 在主线程中更新UI
            self.root.after(0, self._update_ui_after_download, False)
    
    def _update_ui_after_download(self, success):
        """下载完成后更新UI"""
        self.download_button.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("下载完成")
            self.progress_var.set(100)
            messagebox.showinfo("成功", "视频下载和信息采集已完成")
        else:
            self.status_var.set("下载失败")
            self.progress_var.set(0)
            messagebox.showerror("失败", "视频下载或信息采集失败，请查看日志")
    
    def login(self):
        """执行登录操作"""
        # 禁用登录按钮，避免重复点击
        self.login_button.config(state=tk.DISABLED)
        self.status_var.set("正在登录...")
        
        # 在新线程中执行登录，避免界面卡顿
        threading.Thread(target=self._login_thread, daemon=True).start()
    
    def _login_thread(self):
        """登录线程"""
        try:
            # 调用控制器执行登录
            result = self.controller.login()
            
            # 在主线程中更新UI
            self.root.after(0, self._update_ui_after_login, result)
            
        except Exception as e:
            print(f"登录过程中出错: {e}")
            # 在主线程中更新UI
            self.root.after(0, self._update_ui_after_login, False)
    
    def _update_ui_after_login(self, success):
        """登录完成后更新UI"""
        self.login_button.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("已登录")
            messagebox.showinfo("成功", "登录成功")
        else:
            self.status_var.set("登录失败")
            messagebox.showerror("失败", "登录失败，请查看日志")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
    
    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()