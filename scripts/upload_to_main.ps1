# upload_to_main.ps1 - Upload transcoded video to main server
param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile
)

$mainServer = "38.47.218.137"
$mainUser = "root"
$uploadPath = "/www/wwwroot/video-app/backend/uploads/videos/"
$keyFile = "C:\server_key"
$logFile = "D:\VideoTranscode\logs\upload.log"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
    Write-Host "$timestamp - $Message"
}

Write-Log "=========================================="
Write-Log "Starting upload: $VideoFile"

# Check if video file exists
if (-not (Test-Path $VideoFile)) {
    Write-Log "ERROR: Video file not found: $VideoFile"
    exit 1
}

$fileName = Split-Path $VideoFile -Leaf
$fileSize = (Get-Item $VideoFile).Length / 1MB
Write-Log "File: $fileName"
Write-Log "Size: $([math]::Round($fileSize, 2)) MB"

# Check if SSH key exists
if (-not (Test-Path $keyFile)) {
    Write-Log "ERROR: SSH key not found: $keyFile"
    Write-Log "Please create the key file first"
    exit 1
}

# Upload using scp
Write-Log "Uploading to main server..."
$startTime = Get-Date

try {
    # Use OpenSSH scp
    $scpArgs = @(
        "-i", $keyFile,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        $VideoFile,
        "${mainUser}@${mainServer}:${uploadPath}"
    )
    
    $process = Start-Process -FilePath "C:\Windows\System32\OpenSSH\scp.exe" -ArgumentList $scpArgs -NoNewWindow -Wait -PassThru
    
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
        Write-Log "=========================================="
        exit 1
    }
} catch {
    Write-Log "ERROR: Upload exception: $_"
    Write-Log "=========================================="
    exit 1
}
