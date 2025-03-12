import os
import sys
import tkinter as tk
from tk
import time
import threading
from tkinter import ttk, messagebox, filedialog, scrolledtext
import qrcode
from PIL import Image, ImageTk
import webbrowser

class VideoCollectorGUI:
    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("短视频内容采集系统")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 设置主题颜色
        self.bg_color = "#f5f5f5"
        self.accent_color = "#4285f4"
        self.root.configure(bg=self.bg_color)
        
        # 创建UI元素
        self._create_menu()
        self._create_main_frame()
        self._create_status_bar()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 任务线程
        self.task_thread = None
        self.is_running = False
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置下载目录", command=self._set_download_path)
        file_menu.add_command(label="设置Excel文件", command=self._set_excel_path)
        file_menu.add_separator()
        file_menu.add_command(label="打开下载目录", command=self._open_download_folder)
        file_menu.add_command(label="打开Excel文件", command=self._open_excel_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 账号菜单
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="抖音登录", command=lambda: self._show_login_dialog("douyin"))
        account_menu.add_command(label="小红书登录", command=lambda: self._show_login_dialog("xiaohongshu"))
        account_menu.add_command(label="快手登录", command=lambda: self._show_login_dialog("kuaishou"))
        account_menu.add_command(label="视频号登录", command=lambda: self._show_login_dialog("weixin"))
        menubar.add_cascade(label="账号", menu=account_menu)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="API设置", command=self._show_api_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _create_main_frame(self):
        """创建主界面"""
        main_frame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题
        title_label = ttk.Label(main_frame, text="短视频内容采集系统", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 平台选择
        platform_frame = ttk.Frame(main_frame)
        platform_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(platform_frame, text="平台:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.platform_var = tk.StringVar(value="douyin")
        platforms = [("抖音", "douyin"), ("小红书", "xiaohongshu"), ("快手", "kuaishou"), ("视频号", "weixin")]
        
        for i, (name, value) in enumerate(platforms):
            rb = ttk.Radiobutton(platform_frame, text=name, value=value, variable=self.platform_var)
            rb.pack(side=tk.LEFT, padx=(10 if i > 0 else 0, 0))
        
        # 链接输入
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(input_frame, text="输入链接:").pack(anchor=tk.W, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.insert(tk.END, "在此粘贴短视频链接，每行一个...")
        self.input_text.bind("<FocusIn>", self._on_input_focus_in)
        self.input_text.bind("<FocusOut>", self._on_input_focus_out)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.download_btn = ttk.Button(button_frame, text="开始下载", command=self._start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空输入", command=self._clear_input)
        self.clear_btn.pack(side=tk.LEFT)
        
        # 日志区域
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="执行日志:").pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_text = tk.StringVar()
        self.status_text.set("就绪")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_text, anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # 登录状态指示
        self.login_status = {
            "douyin": tk.StringVar(value="未登录"),
            "xiaohongshu": tk.StringVar(value="未登录"),
            "kuaishou": tk.StringVar(value="未登录"),
            "weixin": tk.StringVar(value="未登录")
        }
        
        for platform, status_var in self.login_status.items():
            frame = ttk.Frame(self.status_bar)
            frame.pack(side=tk.RIGHT, padx=(0, 10))
            
            platform_names = {"douyin": "抖音", "xiaohongshu": "小红书", "kuaishou": "快手", "weixin": "视频号"}
            
            ttk.Label(frame, text=f"{platform_names[platform]}:").pack(side=tk.LEFT)
            status_label = ttk.Label(frame, textvariable=status_var)
            status_label.pack(side=tk.LEFT, padx=(2, 0))
    
    def _on_input_focus_in(self, event):
        """输入框获得焦点时清除提示"""
        if self.input_text.get("1.0", tk.END).strip() == "在此粘贴短视频链接，每行一个...":
            self.input_text.delete("1.0", tk.END)
    
    def _on_input_focus_out(self, event):
        """输入框失去焦点时显示提示"""
        if not self.input_text.get("1.0", tk.END).strip():
            self.input_text.insert("1.0", "在此粘贴短视频链接，每行一个...")
    
    def _clear_input(self):
        """清空输入框"""
        self.input_text.delete("1.0", tk.END)
    
    def _set_download_path(self):
        """设置下载目录"""
        current_path = self.controller.config.get("download_path")
        new_path = filedialog.askdirectory(initialdir=current_path)
        
        if new_path:
            self.controller.config.set("download_path", new_path)
            self._log_message(f"下载目录已设置为: {new_path}")
    
    def _set_excel_path(self):
        """设置Excel文件路径"""
        current_path = self.controller.config.get("excel_path")
        new_path = filedialog.asksaveasfilename(
            initialdir=os.path.dirname(current_path),
            initialfile=os.path.basename(current_path),
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        
        if new_path:
            self.controller.config.set("excel_path", new_path)
            self._log_message(f"Excel文件已设置为: {new_path}")
    
    def _open_download_folder(self):
        """打开下载目录"""
        path = self.controller.config.get("download_path")
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f"open {path}")
            else:
                os.system(f"xdg-open {path}")
        else:
            messagebox.showerror("错误", "下载目录不存在")
    
    def _open_excel_file(self):
        """打开Excel文件"""
        path = self.controller.config.get("excel_path")
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f"open {path}")
            else:
                os.system(f"xdg-open {path}")
        else:
            messagebox.showerror("错误", "Excel文件不存在")
    
    def _show_login_dialog(self, platform):
        """显示登录对话框"""
        login_window = tk.Toplevel(self.root)
        login_window.title(f"{platform.capitalize()} 登录")
        login_window.geometry("400x500")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        
        frame = ttk.Frame(login_window, padding=(20, 20, 20, 20))
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"请使用{platform}APP扫描以下二维码登录", font=("Arial", 12)).pack(pady=(0, 20))
        
        # 创建二维码
        qr_frame = ttk.Frame(frame)
        qr_frame.pack(pady=(0, 20))
        
        loading_label = ttk.Label(qr_frame, text="加载中...")
        loading_label.pack()
        
        # 在线程中获取登录二维码
        def get_qr_code():
            # 模拟获取二维码URL
            url = f"https://example.com/login?platform={platform}&t={int(time.time())}"
            
            # 生成二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((200, 200), Image.LANCZOS)
            
            # 显示二维码
            photo = ImageTk.PhotoImage(qr_img)
            
            self.root.after(0, lambda: [
                loading_label.destroy(),
                ttk.Label(qr_frame, image=photo).pack(),
                qr_frame.image = photo  # 保持引用
            ])
        
        threading.Thread(target=get_qr_code, daemon=True).start()
        
        ttk.Label(frame, text="提示：扫描二维码后，请在APP中确认登录").pack()
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(button_frame, text="完成登录", command=lambda: self._confirm_login(platform, login_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=login_window.destroy).pack(side=tk.LEFT)
    
    def _confirm_login(self, platform, window):
        """确认登录成功"""
        # 模拟登录成功
        self.login_status[platform].set("已登录")
        self._log_message(f"{platform}平台登录成功")
        window.destroy()
    
    def _show_api_settings(self):
        """显示API设置对话框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("API设置")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        frame = ttk.Frame(settings_window, padding=(20, 20, 20, 20))
        frame.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 百度API设置
        baidu_frame = ttk.Frame(notebook, padding=(10, 10, 10, 10))
        notebook.add(baidu_frame, text="百度语音识别")
        
        ttk.Label(baidu_frame, text="百度语音识别API设置", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        baidu_enable_var = tk.BooleanVar(value=self.controller.subtitle_extractor.baidu_api.get('enable', False))
        ttk.Checkbutton(baidu_frame, text="启用百度语音识别", variable=baidu_enable_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(baidu_frame, text="App ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        baidu_app_id = tk.StringVar(value=self.controller.subtitle_extractor.baidu_api.get('app_id', ''))
        ttk.Entry(baidu_frame, textvariable=baidu_app_id, width=40).grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(baidu_frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        baidu_api_key = tk.StringVar(value=self.controller.subtitle_extractor.baidu_api.get('api_key', ''))
        ttk.Entry(baidu_frame, textvariable=baidu_api_key, width=40).grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(baidu_frame, text="Secret Key:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        baidu_secret_key = tk.StringVar(value=self.controller.subtitle_extractor.baidu_api.get('secret_key', ''))
        ttk.Entry(baidu_frame, textvariable=baidu_secret_key, width=40).grid(row=4, column=1, sticky=tk.W, pady=(0, 5))
        
        # 讯飞API设置
        xunfei_frame = ttk.Frame(notebook, padding=(10, 10, 10, 10))
        notebook.add(xunfei_frame, text="讯飞语音识别")
        
        ttk.Label(xunfei_frame, text="讯飞语音识别API设置", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        xunfei_enable_var = tk.BooleanVar(value=self.controller.subtitle_extractor.xunfei_api.get('enable', False))
        ttk.Checkbutton(xunfei_frame, text="启用讯飞语音识别", variable=xunfei_enable_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(xunfei_frame, text="App ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        xunfei_app_id = tk.StringVar(value=self.controller.subtitle_extractor.xunfei_api.get('app_id', ''))
        ttk.Entry(xunfei_frame, textvariable=xunfei_app_id, width=40).grid(row=2, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(xunfei_frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        xunfei_api_key = tk.StringVar(value=self.controller.subtitle_extractor.xunfei_api.get('api_key', ''))
        ttk.Entry(xunfei_frame, textvariable=xunfei_api_key, width=40).grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(xunfei_frame, text="API Secret:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        xunfei_api_secret = tk.StringVar(value=self.controller.subtitle_extractor.xunfei_api.get('api_secret', ''))
        ttk.Entry(xunfei_frame, textvariable=xunfei_api_secret, width=40).grid(row=4, column=1, sticky=tk.W, pady=(0, 5))
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_settings():
            # 保存百度API设置
            self.controller.subtitle_extractor.baidu_api.update({
                'enable': baidu_enable_var.get(),
                'app_id': baidu_app_id.get(),
                'api_key': baidu_api_key.get(),
                'secret_key': baidu_secret_key.get()
            })
            
            # 保存讯飞API设置
            self.controller.subtitle_extractor.xunfei_api.update({
                'enable': xunfei_enable_var.get(),
                'app_id': xunfei_app_id.get(),
                'api_key': xunfei_api_key.get(),
                'api_secret': xunfei_api_secret.get()
            })
            
            # 保存配置
            self.controller.subtitle_extractor.save_api_config()
            messagebox.showinfo("成功", "API设置已保存")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def _show_help(self):
        """显示使用说明"""
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        
        frame = ttk.Frame(help_window, padding=(20, 20, 20, 20))
        frame.pack(fill=tk.BOTH, expand=True)
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """# 短视频内容采集系统使用说明

## 基本使用
1. 选择要下载的短视频平台（抖音、小红书、快手、视频号）
2. 复制短视频链接，粘贴到输入框（可一次粘贴多个链接，每行一个）
3. 点击"开始下载"按钮，系统会自动下载视频并提取信息

## 设置说明
- 文件 → 设置下载目录：设置视频保存的位置
- 文件 → 设置Excel文件：设置信息导出的Excel文件路径
- 账号 → 各平台登录：当遇到需要登录的内容时，可以在此处登录
- 设置 → API设置：配置语音识别API，用于提取无字幕视频的文字内容

## 注意事项
- 首次使用时，建议先设置下载目录和Excel文件路径
- 下载受版权保护的内容仅用于个人学习和研究，请勿用于商业用途
- 批量下载时建议不要一次性下载过多内容，以免被平台限制
- 若遇到下载失败，可能是因为内容需要登录查看或已被删除

## 技术支持
如有问题，请联系开发者获取技术支持。
"""
        
        text.insert(tk.END, help_content)
        text.config(state=tk.DISABLED)
    
    def _show_about(self):
        """显示关于信息"""
        messagebox.showinfo(
            "关于",
            "短视频内容采集系统 v1.0\n\n"
            "本程序用于采集短视频平台内容，仅供学习和研究使用。\n"
            "请勿用于商业用途，遵守相关平台的使用条款。"
        )
    
    def _start_download(self):
        """开始下载处理"""
        if self.is_running:
            messagebox.showinfo("提示", "正在处理中，请等待当前任务完成")
            return
        
        # 获取输入文本
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text or input_text == "在此粘贴短视频链接，每行一个...":
            messagebox.showinfo("提示", "请输入短视频链接")
            return
        
        # 获取平台
        platform = self.platform_var.get()
        
        # 分割链接
        links = [link.strip() for link in input_text.split("\n") if link.strip()]
        
        if not links:
            messagebox.showinfo("提示", "请输入有效的短视频链接")
            return
        
        # 开始处理
        self.is_running = True
        self.download_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        self._log_message("开始处理，共 {} 个链接...".format(len(links)))
        
        # 在线程中执行下载任务
        self.task_thread = threading.Thread(
            target=self._process_links,
            args=(platform, links),
            daemon=True
        )
        self.task_thread.start()
    
    def _process_links(self, platform, links):
        """处理链接列表"""
        total = len(links)
        success_count = 0
        
        for i, link in enumerate(links):
            try:
                # 更新进度
                progress = (i / total) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda msg=f"正在处理第 {i+1}/{total} 个链接...": self.status_text.set(msg))
                
                # 处理单个链接
                self.root.after(0, lambda msg=f"正在解析链接: {link}": self._log_message(msg))
                result = self.controller.process_link(link, platform)
                
                if result['success']:
                    success_count += 1
                    self.root.after(0, lambda msg=f"成功: {result.get('message', '下载完成')}": self._log_message(msg))
                else:
                    self.root.after(0, lambda msg=f"失败: {result.get('message', '未知错误')}": self._log_message(msg))
                    
                    # 检查是否需要登录
                    if result.get('need_login'):
                        self.root.after(0, lambda p=platform: self._show_login_required(p))
            except Exception as e:
                self.root.after(0, lambda msg=f"错误: {str(e)}": self._log_message(msg))
        
        # 更新最终状态
        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda msg=f"处理完成，成功: {success_count}/{total}": self.status_text.set(msg))
        self.root.after(0, lambda msg=f"全部处理完成，成功: {success_count}/{total}": self._log_message(msg))
        
        # 重置状态
        self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.clear_btn.config(state=tk.NORMAL))
        self.is_running = False
    
    def _show_login_required(self, platform):
        """显示需要登录的提示"""
        if messagebox.askyesno("需要登录", f"该内容需要登录{platform}账号才能查看，是否现在登录？"):
            self._show_login_dialog(platform)
    
    def _log_message(self, message):
        """记录日志消息"""
        self.log_text.config(state=tk.NORMAL)
        
        # 添加时间戳
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        # 滚动到最新消息
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _on_close(self):
        """关闭窗口处理"""
        if self.is_running:
            if not messagebox.askyesno("确认", "任务正在进行中，确定要退出吗？"):
                return
        
        self.root.destroy()
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()