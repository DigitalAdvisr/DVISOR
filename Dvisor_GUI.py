import customtkinter as ctk
import threading, queue, time, os, re, ctypes, subprocess
import urllib.request, urllib.error
import concurrent.futures
import win32clipboard
import yt_dlp

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)
DIRECT_EXTS = ('.zip', '.rar', '.7z', '.exe', '.msi', '.apk', '.pdf', '.iso', '.mp3', '.png', '.jpg', '.jpeg', '.mkv', '.csv', '.txt')

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint

class DvisorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro - Universal IDM Engine")
        self.geometry("650x550")
        self.resizable(False, False)
        
        self.header = ctk.CTkLabel(self, text="DVISOR PRO", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00ffcc")
        self.header.pack(pady=(15, 5))
        
        self.sub_header = ctk.CTkLabel(self, text="Universal Multi-Thread Downloader • Auto-Catch Links", font=ctk.CTkFont(size=12))
        self.sub_header.pack(pady=(0, 15))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=600, height=430)
        self.scroll_frame.pack(padx=10, pady=10)
        
        self.task_queue = queue.Queue()
        self.history_cache = set()
        
        threading.Thread(target=self.download_manager, daemon=True).start()
        threading.Thread(target=self.clipboard_monitor, daemon=True).start()
        self.after(100, self.process_queue)

    def get_clip_text(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                return text.strip() if isinstance(text, str) else None
            win32clipboard.CloseClipboard()
        except: pass
        return None

    def clipboard_monitor(self):
        last_seq = user32.GetClipboardSequenceNumber()
        while True:
            time.sleep(0.5)
            current_seq = user32.GetClipboardSequenceNumber()
            if current_seq != last_seq:
                last_seq = current_seq
                text = self.get_clip_text()
                if text and URL_RE.fullmatch(text):
                    self.task_queue.put({"type": "new_link", "url": text})

    def process_queue(self):
        while not self.task_queue.empty():
            task = self.task_queue.get()
            if task["type"] == "new_link":
                url = task["url"]
                if url in self.history_cache:
                    self.add_ui_task(url, duplicate=True)
                else:
                    self.history_cache.add(url)
                    ui_frame, progress_var, status_label, pb_widget = self.add_ui_task(url)
                    threading.Thread(target=self.route_download, args=(url, ui_frame, progress_var, status_label, pb_widget), daemon=True).start()
            
            elif task["type"] == "update_progress":
                task["var"].set(task["value"])
                task["label"].configure(text=task["text"])
                if "color" in task and task["pb"]:
                    task["pb"].configure(progress_color=task["color"])
                    
            elif task["type"] == "finish_task":
                task["var"].set(task["value"])
                task["label"].configure(text=task["text"])
                if "color" in task and task["pb"]: task["pb"].configure(progress_color=task["color"])
                
                btn_frame = ctk.CTkFrame(task["frame"], fg_color="transparent")
                btn_frame.pack(fill="x", padx=10, pady=(0, 10))
                path = task["path"]
                btn_open = ctk.CTkButton(btn_frame, text="📁 Open Folder", width=120, height=28, fg_color="#333333", hover_color="#444444", command=lambda p=path: self.open_folder(p))
                btn_open.pack(side="left", padx=(0, 10))
                btn_del = ctk.CTkButton(btn_frame, text="❌ Clear", width=80, height=28, fg_color="#662222", hover_color="#883333", command=lambda f=task["frame"]: f.destroy())
                btn_del.pack(side="left")

        self.after(100, self.process_queue)

    def add_ui_task(self, url, duplicate=False):
        frame = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        frame.pack(fill="x", pady=5, padx=5)
        display_url = (url[:55] + "...") if len(url) > 55 else url
        lbl = ctk.CTkLabel(frame, text=display_url, font=ctk.CTkFont(size=12, weight="bold"))
        lbl.pack(anchor="w", padx=10, pady=(10, 0))
        
        if duplicate:
            status = ctk.CTkLabel(frame, text="Already Downloaded - Skipped", text_color="#ff4444")
            status.pack(anchor="w", padx=10, pady=(0, 10))
            return None
            
        progress_var = ctk.DoubleVar()
        pb = ctk.CTkProgressBar(frame, variable=progress_var, progress_color="#00ffcc")
        pb.pack(fill="x", padx=10, pady=5)
        pb.set(0)
        
        status = ctk.CTkLabel(frame, text="Initializing...", text_color="#aaaaaa")
        status.pack(anchor="w", padx=10, pady=(0, 10))
        return frame, progress_var, status, pb

    def route_download(self, url, ui_frame, progress_var, status_label, pb_widget):
        clean_url = url.split('?')[0].lower()
        if any(clean_url.endswith(ext) for ext in DIRECT_EXTS):
            self.download_direct_file(url, ui_frame, progress_var, status_label, pb_widget)
        else:
            self.download_media_file(url, ui_frame, progress_var, status_label, pb_widget)

    def download_direct_file(self, url, ui_frame, progress_var, status_label, pb_widget):
        try:
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp:
                file_size = int(resp.headers.get('Content-Length', 0))
                accept_ranges = resp.headers.get('Accept-Ranges', 'none')
            
            filename = url.split('/')[-1].split('?')[0]
            if not filename: filename = f"File_{int(time.time())}.dat"
            output_path = os.path.join(DOWNLOAD_FOLDER, filename)
            
            if file_size > 0 and accept_ranges.lower() == 'bytes':
                with open(output_path, 'wb') as f: f.truncate(file_size)
                downloaded = [0]
                start_time = time.time()
                
                def update_prog(chunk_size):
                    downloaded[0] += chunk_size
                    p_val = downloaded[0] / file_size
                    elapsed = time.time() - start_time
                    speed = (downloaded[0] / elapsed) / (1024*1024) if elapsed > 0 else 0
                    text = f"Downloading: {p_val*100:.1f}% | Speed: {speed:.2f} MiB/s | [10 Threads IDM Mode]"
                    self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": p_val, "text": text, "color": "#00ffcc"})

                def download_chunk(start, end):
                    req_chunk = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}', 'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_chunk) as resp_chunk, open(output_path, 'r+b') as f:
                        f.seek(start)
                        while True:
                            chunk = resp_chunk.read(8192)
                            if not chunk: break
                            f.write(chunk)
                            update_prog(len(chunk))

                chunk_size = file_size // 10
                futures = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    for i in range(10):
                        start = i * chunk_size
                        end = start + chunk_size - 1 if i < 9 else file_size - 1
                        futures.append(executor.submit(download_chunk, start, end))
                concurrent.futures.wait(futures)
            else:
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": "Starting Single-Thread Download...", "color": "#00ffcc"})
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as resp, open(output_path, 'wb') as f:
                    downloaded, start_time = 0, time.time()
                    while True:
                        chunk = resp.read(8192*4)
                        if not chunk: break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if file_size:
                            p_val = downloaded / file_size
                            elapsed = time.time() - start_time
                            speed = (downloaded / elapsed) / (1024*1024) if elapsed > 0 else 0
                            text = f"Downloading: {p_val*100:.1f}% | Speed: {speed:.2f} MiB/s | [Single Thread]"
                            self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": p_val, "text": text, "color": "#00ffcc"})
            
            self.task_queue.put({"type": "finish_task", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Completed! Saved to Dvisor folder.", "color": "#00cc66", "frame": ui_frame, "path": output_path})
        except Exception as e:
            self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": f"Error: {str(e)[:55]}", "color": "#ff4444"})

    def download_media_file(self, url, ui_frame, progress_var, status_label, pb_widget):
        output_tmpl = os.path.join(DOWNLOAD_FOLDER, f"Media_{int(time.time())}.%(ext)s")
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        def hook(d):
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%','').strip()
                speed = ansi_escape.sub('', d.get('_speed_str', '~'))
                try: p_val = float(p_str) / 100.0
                except: p_val = 0
                text = f"Downloading: {p_str}% | Speed: {speed} | [HLS Media Mode]"
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": p_val, "text": text, "color": "#00ffcc"})
            elif d['status'] == 'finished':
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Merging Audio & Video... Please Wait", "color": "#ff9900"})

        base_opts = {
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
            'outtmpl': output_tmpl,
            'concurrent_fragment_downloads': 10,
            'progress_hooks': [hook],
            'quiet': True, 'noprogress': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
        }
        
        final_file = ""
        success = False
        opts_with_cookies = base_opts.copy()
        opts_with_cookies['cookiesfrombrowser'] = ('chrome',)

        try:
            with yt_dlp.YoutubeDL(opts_with_cookies) as ydl:
                info = ydl.extract_info(url, download=True)
                final_file = ydl.prepare_filename(info)
                success = True
        except: pass 

        if not success:
            try:
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": "Chrome locked. Retrying directly...", "color": "#ff4444"})
                with yt_dlp.YoutubeDL(base_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    final_file = ydl.prepare_filename(info)
                    success = True
            except Exception as e2:
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": f"Error: {str(e2).split(chr(10))[0][:55]}", "color": "#ff4444"})

        if success:
            if not final_file.endswith('.mp4'): final_file = final_file.rsplit('.', 1)[0] + '.mp4'
            self.task_queue.put({"type": "finish_task", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Completed! Saved to Dvisor folder.", "color": "#00cc66", "frame": ui_frame, "path": final_file})

    def open_folder(self, path):
        if os.path.exists(path): subprocess.Popen(rf'explorer /select,"{path}"')
        else: subprocess.Popen(rf'explorer "{DOWNLOAD_FOLDER}"')

    def download_manager(self):
        while True: time.sleep(1)

if __name__ == "__main__":
    app = DvisorApp()
    app.mainloop()
