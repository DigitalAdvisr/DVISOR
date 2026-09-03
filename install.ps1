Write-Host "Installing Dvisor Pro (Aria2 Engine)..."
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

$TargetDir = Join-Path -Path $env:USERPROFILE -ChildPath "Downloads\Video\Dvisor"
if (-not (Test-Path -Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }

try { aria2c -v 2>&1 | Out-Null } catch { winget install --id aria2.aria2 -e --silent | Out-Null }
py -m pip install yt-dlp pywin32 customtkinter --upgrade --quiet | Out-Null

$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_GUI.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/DigitalAdvisr/DVISOR/main/Dvisor_GUI.py?v=999" -OutFile $PyPath -UseBasicParsing

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "Dvisor Pro.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$PyPath`""
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "Setup Complete!"
