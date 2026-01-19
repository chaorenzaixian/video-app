# Watcher Guardian - Auto restart watcher if stopped
# This script runs every minute via scheduled task

$logFile = "D:\VideoTranscode\logs\guardian.log"
$watcherScript = "D:\VideoTranscode\scripts\watcher.ps1"
$lockFile = "D:\VideoTranscode\watcher.lock"

function Write-Log($msg) {
    $time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "$time - $msg" -Encoding UTF8
}

# Check if watcher is running using multiple methods
$watcherRunning = $false

# Method 1: Check lock file and if process exists
if (Test-Path $lockFile) {
    $watcherPid = Get-Content $lockFile -ErrorAction SilentlyContinue
    if ($watcherPid) {
        $proc = Get-Process -Id $watcherPid -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -eq "powershell") {
            $watcherRunning = $true
        }
    }
}

# Method 2: Check for ffmpeg running (means watcher is transcoding)
if (-not $watcherRunning) {
    $ffmpeg = Get-Process ffmpeg -ErrorAction SilentlyContinue
    if ($ffmpeg) {
        $watcherRunning = $true
    }
}

if (-not $watcherRunning) {
    Write-Log "Watcher not running, starting..."
    
    # Remove stale lock file
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    
    # Move stuck files from processing back to input
    $stuckFiles = Get-ChildItem "D:\VideoTranscode\processing" -File -ErrorAction SilentlyContinue
    if ($stuckFiles) {
        $count = ($stuckFiles | Measure-Object).Count
        Write-Log "Moving $count stuck files back to input"
        $stuckFiles | Move-Item -Destination "D:\VideoTranscode\input" -Force
    }
    
    # Clean up incomplete output directories
    Remove-Item "D:\VideoTranscode\output\*" -Recurse -Force -ErrorAction SilentlyContinue
    
    # Start watcher in minimized window
    Start-Process powershell -ArgumentList "-NoExit", "-File", $watcherScript -WindowStyle Minimized
    Write-Log "Watcher started successfully"
}
