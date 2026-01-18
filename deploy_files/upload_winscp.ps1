# upload_to_main.ps1 - Upload using WinSCP
param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile
)

$mainServer = "38.47.218.137"
$mainUser = "root"
$mainPassword = "APnoPrlVoa1abrFJ"
$uploadPath = "/www/wwwroot/video-app/backend/uploads/videos/"
$logFile = "D:\VideoTranscode\logs\upload.log"
$winscpPath = "C:\Program Files\WinSCP\WinSCP.com"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
    Write-Host "$timestamp - $Message"
}

Write-Log "=========================================="
Write-Log "Starting upload: $VideoFile"

if (-not (Test-Path $VideoFile)) {
    Write-Log "ERROR: Video file not found: $VideoFile"
    exit 1
}

if (-not (Test-Path $winscpPath)) {
    Write-Log "ERROR: WinSCP not found at $winscpPath"
    Write-Log "Please run setup_winscp.ps1 first"
    exit 1
}

$fileName = Split-Path $VideoFile -Leaf
$fileSize = (Get-Item $VideoFile).Length / 1MB
Write-Log "File: $fileName"
Write-Log "Size: $([math]::Round($fileSize, 2)) MB"

Write-Log "Uploading to main server..."
$startTime = Get-Date

try {
    # Create WinSCP script
    $scriptContent = @"
option batch abort
option confirm off
open scp://${mainUser}:${mainPassword}@${mainServer}/ -hostkey=*
put "$VideoFile" "$uploadPath"
exit
"@
    
    $scriptFile = [System.IO.Path]::GetTempFileName()
    $scriptContent | Out-File -FilePath $scriptFile -Encoding ASCII
    
    # Run WinSCP
    $process = Start-Process -FilePath $winscpPath -ArgumentList "/script=$scriptFile", "/log=$logFile.winscp" -NoNewWindow -Wait -PassThru
    
    Remove-Item $scriptFile -Force -ErrorAction SilentlyContinue
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($process.ExitCode -eq 0) {
        $speed = $fileSize / $duration
        Write-Log "Upload successful!"
        Write-Log "Duration: $([math]::Round($duration, 2)) seconds"
        Write-Log "Speed: $([math]::Round($speed, 2)) MB/s"
        Write-Log "Remote path: ${mainServer}:${uploadPath}${fileName}"
        Write-Log "=========================================="
        exit 0
    } else {
        Write-Log "ERROR: Upload failed with exit code: $($process.ExitCode)"
        Write-Log "Check log: $logFile.winscp"
        Write-Log "=========================================="
        exit 1
    }
} catch {
    Write-Log "ERROR: Upload exception: $_"
    Write-Log "=========================================="
    exit 1
}
