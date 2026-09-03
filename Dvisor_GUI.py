import customtkinter as ctk
import threading, queue, time, os, re
import ctypes
import win32clipboard
import yt_dlp

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint

class DvisorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro - Advanced Downloader")
        self.geometry("650x500")
        self.resizable(False, False)
        
        self.header = ctk.CTkLabel(self, text="DVISOR PRO", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00ffcc")
        self.header.pack(pady=(15, 5))
        
        self.sub_header = ctk.CTkLabel(self, text="Monitoring Clipboard • Advanced Multi-Thread Downloader", font=ctk.CTkFont(size=12))
        self.sub_header.pack(pady=(0, 15))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=600, height=380)
        self.scroll_frame.pack(padx=10, pady=10)
        
        self.task_queue = queue.Queue()
        self.history_cache = set()
        self.worker_thread = threading.Thread(target=self.download_manager, daemon=True)
        self.worker_thread.start()
        
        self.clip_thread = threading.Thread(target=self.clipboard_monitor, daemon=True)
        self.clip_thread.start()
        
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
                    threading.Thread(target=self.execute_download, args=(url, ui_frame, progress_var, status_label, pb_widget), daemon=True).start()
            elif task["type"] == "update_progress":
                task["var"].set(task["value"])
                task["label"].configure(text=task["text"])
                if "color" in task and task["pb"]:
                    task["pb"].configure(progress_color=task["color"])
        self.after(100, self.process_queue)

    def add_ui_task(self, url, duplicate=False):
        frame = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
        frame.pack(fill="x", pady=5, padx=5)
        
        display_url = (url[:50] + "...") if len(url) > 50 else url
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

    def execute_download(self, url, ui_frame, progress_var, status_label, pb_widget):
        output_tmpl = os.path.join(DOWNLOAD_FOLDER, f"Dvisor_{int(time.time())}.%(ext)s")
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        def hook(d):
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%','').strip()
                speed = ansi_escape.sub('', d.get('_speed_str', '~'))
                eta = ansi_escape.sub('', d.get('_eta_str', '~'))
                try: p_val = float(p_str) / 100.0
                except: p_val = 0
                
                detail_text = f"Downloading: {p_str}% | Speed: {speed} | ETA: {eta} | [10 Threads]"
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": p_val, "text": detail_text, "color": "#00ffcc"})
            
            elif d['status'] == 'finished':
                # Color changes to Golden/Orange indicating Merging phase
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Merging Audio & Video... Please Wait", "color": "#ff9900"})

        base_opts = {
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
            'outtmpl': output_tmpl,
            'concurrent_fragment_downloads': 10,
            'progress_hooks': [hook],
            'quiet': True,
            'noprogress': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
        }
        
        opts_with_cookies = base_opts.copy()
        opts_with_cookies['cookiesfrombrowser'] = ('chrome',)
        success = False

        try:
            with yt_dlp.YoutubeDL(opts_with_cookies) as ydl:
                ydl.download([url])
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Completed! Saved to Dvisor folder.", "color": "#00cc66"})
                success = True
        except Exception as e:
            pass 

        if not success:
            try:
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": "Chrome locked. Retrying directly...", "color": "#ff4444"})
                with yt_dlp.YoutubeDL(base_opts) as ydl:
                    ydl.download([url])
                    self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 1.0, "text": "Completed! Saved to Dvisor folder.", "color": "#00cc66"})
            except Exception as e2:
                err_msg = str(e2).split('\n')[0][:55]
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "pb": pb_widget, "value": 0, "text": f"Error: {err_msg}", "color": "#ff4444"})

    def download_manager(self):
        while True: time.sleep(1)

if __name__ == "__main__":
    app = DvisorApp()
    app.mainloop()
