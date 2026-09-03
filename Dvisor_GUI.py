import os
import re
import time
import queue
import ctypes
import threading
import subprocess
import customtkinter as ctk
from tkinter import ttk, Menu

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)
DIRECT_EXTS = ('.zip', '.rar', '.exe', '.pdf', '.iso', '.mp3', '.png', '.jpg', '.apk')

class DvisorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro v1.0 - Internet Download Manager")
        self.geometry("1050x650")
        self.minsize(800, 500)
        self.configure(fg_color="#1e1e1e")
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.build_toolbar()
        self.build_sidebar()
        self.build_grid()
        self.update() # Force Instant Render

        self.task_queue = queue.Queue()
        self.history_cache = set()
        
        threading.Thread(target=self.lazy_load_engines, daemon=True).start()
        self.after(100, self.process_queue)

    def build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#2b2b2b")
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        buttons = ["➕ Add URL", "▶ Resume", "⏸ Stop", "❌ Delete", "⚙ Options"]
        for btn_text in buttons:
            btn = ctk.CTkButton(self.toolbar, text=btn_text, width=80, height=45, fg_color="transparent", hover_color="#444444", text_color="white", font=ctk.CTkFont(weight="bold"))
            btn.pack(side="left", padx=5, pady=10)

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#242424")
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Sidebar.Treeview", background="#242424", foreground="white", fieldbackground="#242424", borderwidth=0, rowheight=25, font=("Arial", 10))
        style.map("Sidebar.Treeview", background=[("selected", "#00ffcc")], foreground=[("selected", "black")])

        self.cat_tree = ttk.Treeview(self.sidebar, style="Sidebar.Treeview", show="tree headings")
        self.cat_tree.heading("#0", text="Categories", anchor="w")
        self.cat_tree.column("#0", width=210)

        node_all = self.cat_tree.insert("", "end", text="🌐 All Downloads", open=True)
        for cat in ["Compressed", "Documents", "Music", "Programs", "Video"]:
            self.cat_tree.insert(node_all, "end", text=f"  {cat}")
        
        self.cat_tree.insert("", "end", text="⏳ Unfinished", open=True)
        self.cat_tree.insert("", "end", text="✅ Finished", open=True)
        self.cat_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def build_grid(self):
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="#1e1e1e")
        self.main_area.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.configure("Main.Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", borderwidth=0, rowheight=30)
        style.configure("Main.Treeview.Heading", background="#2b2b2b", foreground="#00ffcc", relief="flat", font=("Arial", 10, "bold"))
        style.map("Main.Treeview", background=[("selected", "#333333")], foreground=[("selected", "white")])
        
        columns = ("File Name", "Size", "Status", "Time Left", "Transfer Rate", "Added On")
        self.tree = ttk.Treeview(self.main_area, columns=columns, show="headings", style="Main.Treeview")
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w")
            if col == "File Name": self.tree.column(col, width=300, anchor="w")
            else: self.tree.column(col, width=100, anchor="w")
            
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.rc_menu = Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#00ffcc", activeforeground="black")
        self.rc_menu.add_command(label="📁 Open Folder")
        self.rc_menu.add_command(label="❌ Remove")
        self.tree.bind("<Button-3>", self.show_rc_menu)

    def show_rc_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.rc_menu.tk_popup(event.x_root, event.y_root)

    def lazy_load_engines(self):
        import win32clipboard
        self.win32clipboard = win32clipboard
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetClipboardSequenceNumber.restype = ctypes.c_uint
        threading.Thread(target=self.clipboard_monitor, daemon=True).start()

    def clipboard_monitor(self):
        last_seq = self.user32.GetClipboardSequenceNumber()
        while True:
            time.sleep(0.5)
            current_seq = self.user32.GetClipboardSequenceNumber()
            if current_seq != last_seq:
                last_seq = current_seq
                try:
                    self.win32clipboard.OpenClipboard()
                    if self.win32clipboard.IsClipboardFormatAvailable(self.win32clipboard.CF_UNICODETEXT):
                        text = self.win32clipboard.GetClipboardData(self.win32clipboard.CF_UNICODETEXT)
                        if text and URL_RE.fullmatch(text.strip()):
                            self.task_queue.put({"type": "new_link", "url": text.strip()})
                    self.win32clipboard.CloseClipboard()
                except: pass

    def process_queue(self):
        while not self.task_queue.empty():
            task = self.task_queue.get()
            if task["type"] == "new_link":
                url = task["url"]
                if url not in self.history_cache:
                    self.history_cache.add(url)
                    filename = url.split('/')[-1].split('?')[0] or f"Download_{int(time.time())}"
                    item_id = self.tree.insert("", "end", values=(filename, "Calculating...", "Connecting...", "-", "-", "Today"))
                    threading.Thread(target=self.route_download, args=(url, item_id, filename), daemon=True).start()
            elif task["type"] == "update":
                self.tree.item(task["item"], values=task["values"])
        self.after(100, self.process_queue)

    def route_download(self, url, item_id, filename):
        clean_url = url.split('?')[0].lower()
        if any(clean_url.endswith(ext) for ext in DIRECT_EXTS):
            self.download_aria2(url, item_id, filename)
        else:
            self.download_ytdlp(url, item_id, filename)

    def download_aria2(self, url, item_id, filename):
        cmd = ["aria2c", "-x", "16", "-s", "16", "--summary-interval=1", "-d", DOWNLOAD_FOLDER, url]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in process.stdout:
                # Parsing Aria2 Output: [#123456 12MiB/50MiB(24%) CN:16 DL:3MiB ETA:12s]
                match = re.search(r'\((\d+)%\).*?DL:([^ ]+).*?ETA:([^ ]+)', line)
                if match:
                    pct, speed, eta = match.group(1), match.group(2), match.group(3)
                    self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "Unknown", f"Downloading ({pct}%)", eta, speed, "Today")})
            process.wait()
            if process.returncode == 0:
                self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "Completed", "Done", "-", "-", "Today")})
            else:
                self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "-", "Error", "-", "-", "Today")})
        except Exception as e:
            self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "-", "Aria2 Missing", "-", "-", "Today")})

    def download_ytdlp(self, url, item_id, filename):
        import yt_dlp
        output_tmpl = os.path.join(DOWNLOAD_FOLDER, f"Media_{int(time.time())}.%(ext)s")
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        def hook(d):
            if d['status'] == 'downloading':
                pct = d.get('_percent_str', '0%').replace('%','').strip()
                speed = ansi_escape.sub('', d.get('_speed_str', '~'))
                eta = ansi_escape.sub('', d.get('_eta_str', '~'))
                size = ansi_escape.sub('', d.get('_total_bytes_estimate_str', '~'))
                self.task_queue.put({"type": "update", "item": item_id, "values": (filename, size, f"Downloading ({pct}%)", eta, speed, "Today")})
            elif d['status'] == 'finished':
                self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "-", "Merging...", "-", "-", "Today")})

        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': output_tmpl,
            'concurrent_fragment_downloads': 10,
            'progress_hooks': [hook],
            'quiet': True, 'noprogress': True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
            self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "-", "Completed", "-", "-", "Today")})
        except:
            self.task_queue.put({"type": "update", "item": item_id, "values": (filename, "-", "Failed", "-", "-", "Today")})

if __name__ == "__main__":
    app = DvisorPro()
    app.mainloop()
