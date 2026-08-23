# ===================================================
# DVISOR FILELESS AUTO-SETUP (FIXED PATHS)
# ===================================================
Write-Host "===================================================" -ForegroundColor Green
Write-Host "DVISOR ONE-CLICK SETUP INITIALIZING..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

# 1. PROCESS KILLER
Write-Host "[1/6] Cleaning up old processes..."
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

# 2. FOLDER CREATION (Using Native Environment Variables)
Write-Host "[2/6] Preparing System Directories..."
$TargetDir = Join-Path -Path $env:USERPROFILE -ChildPath "Downloads\Video\Dvisor"
if (-not (Test-Path -Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# 3. PYTHON SKIP LOGIC
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

# 4. FFMPEG SKIP LOGIC
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

# PATH VARIABLE REFRESH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 5. PIP LIBRARIES
Write-Host "[5/6] Verifying Python Libraries (yt-dlp, pywin32)..."
py -m pip install yt-dlp pywin32 --upgrade --quiet | Out-Null

# 6. EXTRACT PYTHON CORE & SHORTCUT
Write-Host "[6/6] Building Dvisor Core & Auto-Start Shortcut..."
$PyCode = @"
import ctypes, logging, os, re, struct, subprocess, sys, time, winsound, glob
from datetime import datetime
import win32clipboard

DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "Video", "Dvisor")
LOG_FILE = os.path.join(DOWNLOAD_FOLDER, "V3_Downloader.log")
MAX_HEIGHT = 720

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040
CF_HDROP = 15

kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_bool
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
kernel32.GlobalFree.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.GetClipboardSequenceNumber.restype = ctypes.c_uint

URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.IGNORECASE)

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

def update_folder_status(status_msg):
    for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "!STATUS_*.txt")):
        try: os.remove(f)
        except: pass
    if status_msg:
        try: open(os.path.join(DOWNLOAD_FOLDER, f"!STATUS_{status_msg}.txt"), 'w').close()
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

def download_and_track(url):
    output_filename = get_next_filename()
    output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
    logging.info(f"Starting Download: {url} -> {output_filename}")
    update_folder_status("1_STARTING_CONNECTION")
    
    format_selector = f"bestvideo[ext=mp4][height<={MAX_HEIGHT}]+bestaudio[ext=m4a]/best[ext=mp4][height<={MAX_HEIGHT}]/best"
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--newline", "--format", format_selector, "--merge-output-format", "mp4", "--output", output_path, url]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    last_pct = -1
    for line in process.stdout:
        if "[download]" in line and "%" in line:
            match = re.search(r'(\d+\.\d+)%', line)
            if match:
                pct = int(float(match.group(1)))
                if pct % 5 == 0 and pct != last_pct:
                    update_folder_status(f"2_DOWNLOADING_{pct}_PERCENT")
                    last_pct = pct
        elif "[Merger]" in line or "[ExtractAudio]" in line or "[VideoConvertor]" in line:
            update_folder_status("3_FINALIZING_FILE_PLEASE_WAIT")
            
    process.wait()
    update_folder_status(None) 
    
    if process.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
        logging.info(f"Success: {output_path}")
        return output_path
    else:
        logging.error("Download or conversion failed.")
        return None

def main():
    logging.info("V3 Background Monitor Started.")
    last_seq = user32.GetClipboardSequenceNumber()
    while True:
        try:
            time.sleep(0.5)
            current_seq = user32.GetClipboardSequenceNumber()
            if current_seq != last_seq:
                last_seq = current_seq
                clip_text = get_clipboard_text()
                if clip_text and URL_RE.fullmatch(clip_text.strip()):
                    final_file = download_and_track(clip_text.strip())
                    if final_file:
                        copy_file_to_clipboard(final_file)
                        notify_success()
                        last_seq = user32.GetClipboardSequenceNumber()
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
"@

$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_Core.py"
Set-Content -Path $PyPath -Value $PyCode -Encoding UTF8 -Force

# Startup shortcut using native APPDATA variable
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
Write-Host "SETUP COMPLETE! Dvisor is active in the background." -ForegroundColor Green
Write-Host "You can safely close this window." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Start-Sleep -Seconds 5
