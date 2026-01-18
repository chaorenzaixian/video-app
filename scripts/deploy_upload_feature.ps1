# Deploy upload feature to transcode server
$server = "198.176.60.121"
$user = "Administrator"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Upload Feature to Transcode Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "1. Upload the SSH key file" -ForegroundColor White
Write-Host "2. Upload the upload script" -ForegroundColor White
Write-Host "3. Upload the updated watcher script" -ForegroundColor White
Write-Host "4. Test the upload functionality" -ForegroundColor White
Write-Host ""

# Step 1: Create SSH key on remote server
Write-Host "[1/4] Creating SSH key on remote server..." -ForegroundColor Yellow

$keyContent = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----
"@

# Create temp file
$tempKey = "temp_key_$([guid]::NewGuid().ToString().Substring(0,8))"
$keyContent | Out-File -FilePath $tempKey -Encoding ASCII

Write-Host "Uploading key file..." -ForegroundColor Gray
echo y | C:\Windows\System32\OpenSSH\scp.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $tempKey ${user}@${server}:C:/server_key 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Key file uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to upload key file" -ForegroundColor Red
    Remove-Item $tempKey -Force -ErrorAction SilentlyContinue
    exit 1
}

Remove-Item $tempKey -Force -ErrorAction SilentlyContinue

# Step 2: Upload upload script
Write-Host ""
Write-Host "[2/4] Uploading upload script..." -ForegroundColor Yellow

if (Test-Path "scripts\upload_to_main.ps1") {
    echo y | C:\Windows\System32\OpenSSH\scp.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL scripts\upload_to_main.ps1 ${user}@${server}:D:/VideoTranscode/scripts/upload_to_main.ps1 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Upload script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to upload script" -ForegroundColor Red
    }
} else {
    Write-Host "Upload script not found locally" -ForegroundColor Red
}

# Step 3: Upload updated watcher script
Write-Host ""
Write-Host "[3/4] Uploading updated watcher script..." -ForegroundColor Yellow

if (Test-Path "scripts\watcher_with_upload.ps1") {
    echo y | C:\Windows\System32\OpenSSH\scp.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL scripts\watcher_with_upload.ps1 ${user}@${server}:D:/VideoTranscode/scripts/watcher.ps1 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Watcher script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to upload watcher script" -ForegroundColor Red
    }
} else {
    Write-Host "Watcher script not found locally" -ForegroundColor Red
}

# Step 4: Test configuration
Write-Host ""
Write-Host "[4/4] Testing configuration..." -ForegroundColor Yellow

Write-Host "Checking if key file exists..." -ForegroundColor Gray
$checkKey = echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${user}@${server} "powershell -Command `"Test-Path C:\server_key`"" 2>&1

if ($checkKey -match "True") {
    Write-Host "Key file exists: C:\server_key" -ForegroundColor Green
} else {
    Write-Host "Key file not found" -ForegroundColor Red
}

Write-Host "Checking if upload script exists..." -ForegroundColor Gray
$checkUpload = echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${user}@${server} "powershell -Command `"Test-Path D:\VideoTranscode\scripts\upload_to_main.ps1`"" 2>&1

if ($checkUpload -match "True") {
    Write-Host "Upload script exists: D:\VideoTranscode\scripts\upload_to_main.ps1" -ForegroundColor Green
} else {
    Write-Host "Upload script not found" -ForegroundColor Red
}

Write-Host "Checking if watcher script exists..." -ForegroundColor Gray
$checkWatcher = echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${user}@${server} "powershell -Command `"Test-Path D:\VideoTranscode\scripts\watcher.ps1`"" 2>&1

if ($checkWatcher -match "True") {
    Write-Host "Watcher script exists: D:\VideoTranscode\scripts\watcher.ps1" -ForegroundColor Green
} else {
    Write-Host "Watcher script not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Test upload: Put a video in D:\VideoTranscode\downloads" -ForegroundColor White
Write-Host "2. Start watcher: powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\watcher.ps1" -ForegroundColor White
Write-Host "3. Check logs: D:\VideoTranscode\logs\upload.log" -ForegroundColor White
Write-Host ""
