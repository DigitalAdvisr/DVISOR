Write-Host "===================================================" -ForegroundColor Green
Write-Host "DVISOR PRO (GUI EDITION) INSTALLER..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

Write-Host "[1/5] Cleaning up old processes..."
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

Write-Host "[2/5] Preparing System Directories..."
$TargetDir = Join-Path -Path $env:USERPROFILE -ChildPath "Downloads\Video\Dvisor"
if (-not (Test-Path -Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Write-Host "[3/5] Verifying Dependencies..."
try { py --version 2>&1 | Out-Null } catch { winget install --id Python.Python.3.11 -e --silent | Out-Null }
try { ffmpeg -version 2>&1 | Out-Null } catch { winget install --id Gyan.FFmpeg -e --silent | Out-Null }

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
py -m pip install yt-dlp pywin32 customtkinter --upgrade --quiet | Out-Null

Write-Host "[4/5] Downloading GUI Engine from GitHub..."
$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_GUI.py"
$RepoUrl = "https://raw.githubusercontent.com/DigitalAdvisr/DVISOR/main/Dvisor_GUI.py"
Invoke-WebRequest -Uri $RepoUrl -OutFile $PyPath -UseBasicParsing

Write-Host "[5/5] Creating Desktop Shortcut..."
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
