import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import imageio
import threading
from pathlib import Path

class GIFGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF生成器")
        self.root.geometry("800x700")
        
        # 变量
        self.selected_images = []
        self.preview_image = None
        self.current_preview_index = 0
        self.is_playing = False
        self.play_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="图片选择", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 单个图片选择按钮
        self.single_img_btn = ttk.Button(file_frame, text="选择单张图片", command=self.select_single_image)
        self.single_img_btn.grid(row=0, column=0, padx=(0, 5))
        
        # 文件夹选择按钮
        self.folder_btn = ttk.Button(file_frame, text="选择图片文件夹", command=self.select_folder)
        self.folder_btn.grid(row=0, column=1, padx=(5, 5))
        
        # 清除按钮
        self.clear_btn = ttk.Button(file_frame, text="清空列表", command=self.clear_images)
        self.clear_btn.grid(row=0, column=2, padx=(5, 0))
        
        # 图片列表框
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建滚动条和列表
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.image_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            height=6,
            selectmode=tk.EXTENDED
        )
        scrollbar.config(command=self.image_listbox.yview)
        
        self.image_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置权重
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 参数设置区域
        param_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="5")
        param_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 每张图片持续时间
        ttk.Label(param_frame, text="每张图片持续时间(秒):").grid(row=0, column=0, sticky=tk.W)
        self.duration_var = tk.DoubleVar(value=0.5)
        duration_spinbox = ttk.Spinbox(
            param_frame, 
            from_=0.1, 
            to=5.0, 
            increment=0.1, 
            textvariable=self.duration_var,
            width=10
        )
        duration_spinbox.grid(row=0, column=1, padx=(5, 10))
        
        # 循环次数
        ttk.Label(param_frame, text="循环次数(0为无限):").grid(row=0, column=2, sticky=tk.W)
        self.loop_var = tk.IntVar(value=0)
        loop_spinbox = ttk.Spinbox(
            param_frame, 
            from_=0, 
            to=100, 
            textvariable=self.loop_var,
            width=10
        )
        loop_spinbox.grid(row=0, column=3, padx=(5, 0))
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="5")
        preview_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=400, height=300)
        self.preview_canvas.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 预览控制按钮
        self.prev_btn = ttk.Button(preview_frame, text="上一张", command=self.show_prev_image)
        self.prev_btn.grid(row=1, column=0, padx=(0, 5), pady=(5, 0))
        
        self.next_btn = ttk.Button(preview_frame, text="下一张", command=self.show_next_image)
        self.next_btn.grid(row=1, column=1, padx=(5, 5), pady=(5, 0))
        
        self.play_btn = ttk.Button(preview_frame, text="播放", command=self.toggle_play)
        self.play_btn.grid(row=1, column=2, padx=(5, 5), pady=(5, 0))
        
        self.stop_btn = ttk.Button(preview_frame, text="停止", command=self.stop_preview)
        self.stop_btn.grid(row=1, column=3, padx=(5, 0), pady=(5, 0))
        
        # 生成按钮
        generate_frame = ttk.Frame(main_frame)
        generate_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        self.generate_btn = ttk.Button(
            generate_frame, 
            text="生成GIF", 
            command=self.generate_gif,
            style='Accent.TButton'
        )
        self.generate_btn.pack()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def select_single_image(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if files:
            for file_path in files:
                if file_path not in self.selected_images:
                    self.selected_images.append(file_path)
            self.update_image_list()
    
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="选择包含图片的文件夹")
        if folder_path:
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
            new_images = []
            
            for file_name in os.listdir(folder_path):
                file_ext = Path(file_name).suffix.lower()
                if file_ext in image_extensions:
                    file_path = os.path.join(folder_path, file_name)
                    if file_path not in self.selected_images:
                        new_images.append(file_path)
            
            # 按文件名排序
            new_images.sort(key=lambda x: os.path.basename(x))
            self.selected_images.extend(new_images)
            self.update_image_list()
    
    def clear_images(self):
        self.selected_images.clear()
        self.update_image_list()
        self.preview_canvas.delete("all")
        self.current_preview_index = 0
    
    def update_image_list(self):
        self.image_listbox.delete(0, tk.END)
        for img_path in self.selected_images:
            self.image_listbox.insert(tk.END, os.path.basename(img_path))
    
    def show_preview(self, index=None):
        if not self.selected_images:
            return
        
        if index is not None:
            self.current_preview_index = index
        else:
            index = self.current_preview_index
        
        if 0 <= index < len(self.selected_images):
            try:
                img_path = self.selected_images[index]
                img = Image.open(img_path)
                
                # 调整大小以适应画布
                canvas_width = 400
                canvas_height = 300
                img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                
                self.preview_image = ImageTk.PhotoImage(img)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(
                    canvas_width//2, 
                    canvas_height//2, 
                    anchor=tk.CENTER, 
                    image=self.preview_image
                )
                
                # 更新状态
                self.status_var.set(f"预览: {os.path.basename(img_path)} ({index + 1}/{len(self.selected_images)})")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def show_prev_image(self):
        if self.selected_images:
            self.current_preview_index = max(0, self.current_preview_index - 1)
            self.show_preview()
    
    def show_next_image(self):
        if self.selected_images:
            self.current_preview_index = min(len(self.selected_images) - 1, self.current_preview_index + 1)
            self.show_preview()
    
    def toggle_play(self):
        if not self.selected_images:
            return
        
        if not self.is_playing:
            self.is_playing = True
            self.play_btn.config(text="暂停")
            self.play_preview()
        else:
            self.is_playing = False
            self.play_btn.config(text="播放")
    
    def play_preview(self):
        if not self.is_playing or not self.selected_images:
            self.is_playing = False
            self.play_btn.config(text="播放")
            return
        
        self.show_preview()
        self.current_preview_index = (self.current_preview_index + 1) % len(self.selected_images)
        
        duration_ms = int(self.duration_var.get() * 1000)
        self.root.after(duration_ms, self.play_preview)
    
    def stop_preview(self):
        self.is_playing = False
        self.play_btn.config(text="播放")
        if self.selected_images:
            self.show_preview()
    
    def generate_gif(self):
        if not self.selected_images:
            messagebox.showwarning("警告", "请先选择要合成的图片！")
            return
        
        output_path = filedialog.asksaveasfilename(
            title="保存GIF文件",
            defaultextension=".gif",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        # 在新线程中生成GIF以避免阻塞UI
        thread = threading.Thread(target=self._generate_gif_thread, args=(output_path,))
        thread.daemon = True
        thread.start()
    
    def _generate_gif_thread(self, output_path):
        try:
            self.status_var.set("正在生成GIF...")
            
            images = []
            for img_path in self.selected_images:
                img = imageio.imread(img_path)
                images.append(img)
            
            duration = self.duration_var.get()
            loop = self.loop_var.get()
            
            # 保存GIF
            imageio.mimsave(
                output_path, 
                images, 
                duration=duration, 
                loop=loop
            )
            
            self.status_var.set(f"GIF已保存到: {output_path}")
            messagebox.showinfo("成功", "GIF生成完成！")
            
        except Exception as e:
            self.status_var.set("就绪")
            messagebox.showerror("错误", f"生成GIF失败: {str(e)}")

def main():
    root = tk.Tk()
    app = GIFGeneratorApp(root)
    
    # 设置窗口关闭事件
    def on_closing():
        app.is_playing = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动时显示第一张图片预览
    root.after(100, lambda: app.show_preview(0) if app.selected_images else None)
    
    root.mainloop()

if __name__ == "__main__":
    main()