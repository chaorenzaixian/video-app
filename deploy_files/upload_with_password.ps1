# upload_to_main.ps1 - Upload transcoded video to main server
param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile
)

$mainServer = "38.47.218.137"
$mainUser = "root"
$mainPassword = "APnoPrlVoa1abrFJ"
$uploadPath = "/www/wwwroot/video-app/backend/uploads/videos/"
$logFile = "D:\VideoTranscode\logs\upload.log"

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

$fileName = Split-Path $VideoFile -Leaf
$fileSize = (Get-Item $VideoFile).Length / 1MB
Write-Log "File: $fileName"
Write-Log "Size: $([math]::Round($fileSize, 2)) MB"

Write-Log "Uploading to main server..."
$startTime = Get-Date

try {
    # Create a temporary expect-like script for password automation
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    
    # Use pscp if available (PuTTY), otherwise try with echo password
    $pscpPath = "C:\Program Files\PuTTY\pscp.exe"
    
    if (Test-Path $pscpPath) {
        # Use PuTTY's pscp with password
        Write-Log "Using pscp for upload..."
        $process = Start-Process -FilePath $pscpPath -ArgumentList "-pw", $mainPassword, "-batch", $VideoFile, "${mainUser}@${mainServer}:${uploadPath}" -NoNewWindow -Wait -PassThru
    } else {
        # Try using scp with password via stdin (may not work on all systems)
        Write-Log "Using scp for upload (you may need to enter password manually)..."
        Write-Log "Password: $mainPassword"
        
        # Create a batch file to automate password input
        $batchFile = [System.IO.Path]::GetTempFileName() + ".bat"
        @"
@echo off
echo $mainPassword | C:\Windows\System32\OpenSSH\scp.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $VideoFile ${mainUser}@${mainServer}:${uploadPath}
"@ | Out-File -FilePath $batchFile -Encoding ASCII
        
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $batchFile -NoNewWindow -Wait -PassThru
        Remove-Item $batchFile -Force -ErrorAction SilentlyContinue
    }
    
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
        Write-Log "Please check if the file was uploaded manually"
        Write-Log "=========================================="
        exit 1
    }
} catch {
    Write-Log "ERROR: Upload exception: $_"
    Write-Log "=========================================="
    exit 1
}
