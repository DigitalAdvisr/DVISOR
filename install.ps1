Write-Host "Installing Dvisor Pro (Aria2 Engine)..."
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

$TargetDir = Join-Path -Path $env:USERPROFILE -ChildPath "Downloads\Video\Dvisor"
if (-not (Test-Path -Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }

try { aria2c -v 2>&1 | Out-Null } catch { winget install --id aria2.aria2 -e --silent | Out-Null }
py -m pip install yt-dlp pywin32 customtkinter --upgrade --quiet | Out-Null

$PyPath = Join-Path -Path $TargetDir -ChildPath "Dvisor_GUI.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/DigitalAdvisr/DVISOR/main/Dvisor_GUI.py" -OutFile $PyPath -UseBasicParsing

# =================================================================
# PERMANENT FIX: SMART PATH FALLBACK ENGINE
# =================================================================
$PathsToCheck = @(
    (Join-Path -Path $env:USERPROFILE -ChildPath "OneDrive\Desktop"),
    [Environment]::GetFolderPath("Desktop"),
    [Environment]::GetFolderPath("CommonDesktopDirectory"),
    (Join-Path -Path $env:PUBLIC -ChildPath "Desktop")
)

$ValidDesktop = ""
foreach ($P in $PathsToCheck) {
    if ([string]::IsNullOrWhiteSpace($P) -eq $false -and (Test-Path -Path $P)) {
        $ValidDesktop = $P
        break
    }
}

# Failsafe: If no desktop exists, force create it to prevent crash
if ([string]::IsNullOrWhiteSpace($ValidDesktop)) {
    $ValidDesktop = Join-Path -Path $env:USERPROFILE -ChildPath "Desktop"
    New-Item -ItemType Directory -Path $ValidDesktop -Force | Out-Null
}

$ShortcutPath = Join-Path -Path $ValidDesktop -ChildPath "Dvisor Pro.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$PyPath`""
$Shortcut.WindowStyle = 1
$Shortcut.Save()

Write-Host "Setup Complete! Shortcut successfully created at: $ValidDesktop"
