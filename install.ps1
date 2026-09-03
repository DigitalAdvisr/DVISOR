# ===================================================
# DVISOR V4.1 - IDM ACCELERATOR MODULE ADDED
# ===================================================
Write-Host "===================================================" -ForegroundColor Green
Write-Host "DVISOR ONE-CLICK SETUP INITIALIZING..." -ForegroundColor Green
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

Write-Host "[5/6] Verifying Python Libraries..."
py -m pip install yt-dlp pywin32 --upgrade --quiet | Out-Null

Write-Host "[6/6] Building V4.1 Core Engine (IDM Accelerator)..."
$PyCode = @"
import ctypes, logging, os, re, struct, subprocess, sys, time, winsound, glob
import win32clipboard
import threading
import queue

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
LOG_FILE = os.path.join(DOWNLOAD_FOLDER, "V4_Downloader.log")
MAX_HEIGHT = 720

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
GMEM_MOVEABLE, GMEM_ZEROINIT, CF_HDROP = 0x0002, 0x0040, 15

kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes, kernel32.GlobalLock.restype = [ctypes.c_void_p], ctypes.c_void_p
kernel32.GlobalUnlock.argtypes, kernel32.GlobalUnlock.restype = [ctypes.c_void_p], ctypes.c_bool
kernel32.GlobalFree.argtypes, kernel32.GlobalFree.restype = [ctypes.c_void_p], ctypes.c_void_p
user32.SetClipboardData.argtypes, user32.SetClipboardData.restype = [ctypes.c_uint, ctypes.c_void_p], ctypes.c_void_p
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint

URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)
download_queue = queue.Queue()

def get_clipboard_text():
    try:
        win32clipboard.OpenClipboard()
        try:
            if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT): return None
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            return text.strip() if isinstance(text, str) else None
        finally:
            win32clipboard.CloseClipboard()
    except Exception: return None

def copy_file_to_clipboard(file_path):
    absolute_path = os.path.abspath(file_path)
    dropfiles = struct.pack("<IiiII", 20, 0, 0, 0, 1)
    payload = dropfiles + absolute_path.encode("utf-16le") + b"\x00\x00\x00\x00"
    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(payload))
    locked_memory = kernel32.GlobalLock(h_global)
    ctypes.memmove(locked_memory, payload, len(payload))
    kernel32.GlobalUnlock(h_global)
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        user32.SetClipboardData(CF_HDROP, h_global)
    finally:
        win32clipboard.CloseClipboard()

def notify_success():
    try:
        winsound.Beep(1100, 180)
        time.sleep(0.08)
        winsound.Beep(1500, 220)
    except: pass

def get_next_filename():
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "Dvisor*.mp4"))
    max_num = 0
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r"Dvisor(\d+)\.mp4", basename, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            if num > max_num: max_num = num
    return f"Dvisor{max_num + 1}.mp4"

def process_download(url):
    output_filename = get_next_filename()
    output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
    logging.info(f"Starting Download: {url} -> {output_filename}")
    
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--cookies-from-browser", "chrome",
        "--no-playlist",
        "--concurrent-fragments", "10",
        "-S", f"vcodec:h264,ext:mp4:m4a,res:{MAX_HEIGHT}",
        "--recode-video", "mp4",
        "--postprocessor-args", "ffmpeg:-pix_fmt yuv420p",
        "--output", output_path,
        url
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    process.wait()
    
    if process.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
        logging.info(f"Success: {output_path}")
        return output_path
    else:
        logging.error(f"Download failed for: {url}")
        return None

def download_worker():
    while True:
        url = download_queue.get()
        if url:
            final_file = process_download(url)
            if final_file:
                copy_file_to_clipboard(final_file)
                notify_success()
        download_queue.task_done()

def main():
    logging.info("V4.1 Multi-Thread Monitor Started.")
    worker = threading.Thread(target=download_worker, daemon=True)
    worker.start()
    
    last_seq = user32.GetClipboardSequenceNumber()
    while True:
        try:
            time.sleep(0.3)
            current_seq = user32.GetClipboardSequenceNumber()
            if current_seq != last_seq:
                last_seq = current_seq
                clip_text = get_clipboard_text()
                if clip_text and URL_RE.fullmatch(clip_text.strip()):
                    logging.info(f"Link added to queue: {clip_text.strip()}")
                    download_queue.put(clip_text.strip())
        except Exception as e:
            logging.error(f"Clipboard Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
"@

$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_Core.py"
Set-Content -Path $PyPath -Value $PyCode -Encoding UTF8 -Force

$ShortcutPath = Join-Path -Path $env:APPDATA -ChildPath "Microsoft\Windows\Start Menu\Programs\Startup\Dvisor_Auto_Downloader.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pyw.exe"
$Shortcut.Arguments = "`"$PyPath`""
$Shortcut.WindowStyle = 7
$Shortcut.Save()

Write-Host "Starting Background Service..." -ForegroundColor Cyan
Start-Process -FilePath "pyw.exe" -ArgumentList "`"$PyPath`"" -WindowStyle Hidden -ErrorAction SilentlyContinue

Write-Host "===================================================" -ForegroundColor Green
Write-Host "SETUP COMPLETE! V4.1 Accelerator Engine is active." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Start-Sleep -Seconds 5
