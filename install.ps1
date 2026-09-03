Write-Host "===================================================" -ForegroundColor Green
Write-Host "DVISOR PRO (GUI EDITION) INITIALIZING..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

Write-Host "[1/6] Cleaning up old processes..."
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

Write-Host "[2/6] Preparing System Directories..."
$TargetDir = Join-Path -Path $env:USERPROFILE -ChildPath "Downloads\Video\Dvisor"
if (-not (Test-Path -Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Write-Host "[3/6] Verifying Python Environment..."
try {
    $pyCheck = py --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      -> Python detected. Skipping installation." -ForegroundColor Yellow
    } else { throw }
} catch {
    Write-Host "      -> Python not found. Installing silently via winget..." -ForegroundColor Cyan
    winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
}

Write-Host "[4/6] Verifying FFmpeg..."
try {
    $ffCheck = ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      -> FFmpeg detected. Skipping installation." -ForegroundColor Yellow
    } else { throw }
} catch {
    Write-Host "      -> FFmpeg not found. Installing silently via winget..." -ForegroundColor Cyan
    winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
}

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "[5/6] Verifying GUI and Core Libraries..."
py -m pip install yt-dlp pywin32 customtkinter --upgrade --quiet | Out-Null

Write-Host "[6/6] Building Dvisor Pro GUI Engine..."
$PyCode = @'
import customtkinter as ctk
import threading, queue, win32clipboard, time, os, re, ctypes, struct
import yt_dlp

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)

kernel32, user32 = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("user32", use_last_error=True)
GMEM_MOVEABLE, GMEM_ZEROINIT, CF_HDROP = 0x0002, 0x0040, 15

kernel32.GlobalAlloc.argtypes, kernel32.GlobalAlloc.restype = [ctypes.c_uint, ctypes.c_size_t], ctypes.c_void_p
kernel32.GlobalLock.argtypes, kernel32.GlobalLock.restype = [ctypes.c_void_p], ctypes.c_void_p
kernel32.GlobalUnlock.argtypes, kernel32.GlobalUnlock.restype = [ctypes.c_void_p], ctypes.c_bool
user32.SetClipboardData.argtypes, user32.SetClipboardData.restype = [ctypes.c_uint, ctypes.c_void_p], ctypes.c_void_p
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint

class DvisorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dvisor Pro - Premium Downloader")
        self.geometry("650x500")
        self.resizable(False, False)
        
        self.header = ctk.CTkLabel(self, text="DVISOR PRO", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00ffcc")
        self.header.pack(pady=(15, 5))
        
        self.sub_header = ctk.CTkLabel(self, text="Monitoring Clipboard • Auto-Download & Copy", font=ctk.CTkFont(size=12))
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
                    ui_frame, progress_var, status_label = self.add_ui_task(url)
                    threading.Thread(target=self.execute_download, args=(url, ui_frame, progress_var, status_label), daemon=True).start()
            elif task["type"] == "update_progress":
                task["var"].set(task["value"])
                task["label"].configure(text=task["text"])
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
        return frame, progress_var, status

    def execute_download(self, url, ui_frame, progress_var, status_label):
        output_tmpl = os.path.join(DOWNLOAD_FOLDER, f"Dvisor_{int(time.time())}.%(ext)s")
        
        def hook(d):
            if d['status'] == 'downloading':
                p_str = d.get('_percent_str', '0%').replace('%','').strip()
                try: p_val = float(p_str) / 100.0
                except: p_val = 0
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "value": p_val, "text": f"Downloading: {p_str}%"})
            elif d['status'] == 'finished':
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "value": 1.0, "text": "Processing Video..."})

        opts = {
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
            'outtmpl': output_tmpl,
            'cookiesfrombrowser': ('chrome',),
            'concurrent_fragment_downloads': 10,
            'progress_hooks': [hook],
            'quiet': True,
            'noprogress': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_file = ydl.prepare_filename(info)
                if not final_file.endswith('.mp4'): final_file = final_file.rsplit('.', 1)[0] + '.mp4'
                
                self.copy_to_clip(final_file)
                self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "value": 1.0, "text": "Completed! Ready in Clipboard."})
        except Exception as e:
            self.task_queue.put({"type": "update_progress", "var": progress_var, "label": status_label, "value": 0, "text": "Download Failed (Check Network/Browser)"})

    def copy_to_clip(self, file_path):
        try:
            absolute_path = os.path.abspath(file_path)
            dropfiles = struct.pack("<IiiII", 20, 0, 0, 0, 1)
            payload = dropfiles + absolute_path.encode("utf-16le") + b"\x00\x00\x00\x00"
            h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(payload))
            ctypes.memmove(kernel32.GlobalLock(h_global), payload, len(payload))
            kernel32.GlobalUnlock(h_global)
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            user32.SetClipboardData(CF_HDROP, h_global)
            win32clipboard.CloseClipboard()
            ctypes.windll.user32.MessageBeep(0)
        except: pass

    def download_manager(self):
        while True: time.sleep(1)

if __name__ == "__main__":
    app = DvisorApp()
    app.mainloop()
'@

$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_GUI.py"
Set-Content -Path $PyPath -Value $PyCode -Encoding UTF8 -Force

# Create Desktop Shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Dvisor Pro.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$PyPath`""
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "Starting Dvisor Pro GUI..." -ForegroundColor Cyan
Start-Process -FilePath "pythonw.exe" -ArgumentList "`"$PyPath`"" -ErrorAction SilentlyContinue

Write-Host "===================================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE! Dvisor Pro is on your Desktop." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Start-Sleep -Seconds 5
