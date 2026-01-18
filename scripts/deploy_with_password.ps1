# Deploy upload feature using password authentication
$server = "198.176.60.121"
$user = "Administrator"
$pass = "jCkMIjNlnSd7f6GM"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploy Upload Feature (Password Auth)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Install plink if not available (part of PuTTY)
Write-Host "Checking for pscp (PuTTY)..." -ForegroundColor Yellow
$pscpPath = "C:\Program Files\PuTTY\pscp.exe"
if (-not (Test-Path $pscpPath)) {
    Write-Host "PuTTY not found. Installing via Chocolatey..." -ForegroundColor Yellow
    choco install putty -y
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install PuTTY. Please install manually from https://www.putty.org/" -ForegroundColor Red
        exit 1
    }
}

# Step 1: Create and upload SSH key
Write-Host ""
Write-Host "[1/4] Creating SSH key file..." -ForegroundColor Yellow

$keyContent = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----
"@

$tempKey = "temp_server_key.txt"
$keyContent | Out-File -FilePath $tempKey -Encoding ASCII

Write-Host "Uploading key file to C:\server_key..." -ForegroundColor Gray
& $pscpPath -pw $pass -batch $tempKey ${user}@${server}:C:/server_key

if ($LASTEXITCODE -eq 0) {
    Write-Host "Key file uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to upload key file" -ForegroundColor Red
}

Remove-Item $tempKey -Force -ErrorAction SilentlyContinue

# Step 2: Upload upload script
Write-Host ""
Write-Host "[2/4] Uploading upload script..." -ForegroundColor Yellow

if (Test-Path "scripts\upload_to_main.ps1") {
    & $pscpPath -pw $pass -batch scripts\upload_to_main.ps1 ${user}@${server}:D:/VideoTranscode/scripts/upload_to_main.ps1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Upload script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to upload script" -ForegroundColor Red
    }
} else {
    Write-Host "Upload script not found" -ForegroundColor Red
}

# Step 3: Upload updated watcher script
Write-Host ""
Write-Host "[3/4] Uploading updated watcher script..." -ForegroundColor Yellow

if (Test-Path "scripts\watcher_with_upload.ps1") {
    & $pscpPath -pw $pass -batch scripts\watcher_with_upload.ps1 ${user}@${server}:D:/VideoTranscode/scripts/watcher.ps1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Watcher script uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to upload watcher script" -ForegroundColor Red
    }
} else {
    Write-Host "Watcher script not found" -ForegroundColor Red
}

# Step 4: Verify files
Write-Host ""
Write-Host "[4/4] Verifying files on remote server..." -ForegroundColor Yellow

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
& $plinkPath -ssh -pw $pass -batch ${user}@${server} "powershell -Command `"Get-ChildItem C:\server_key, D:\VideoTranscode\scripts\upload_to_main.ps1, D:\VideoTranscode\scripts\watcher.ps1 | Select-Object Name, Length`""

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Files deployed:" -ForegroundColor Cyan
Write-Host "- C:\server_key (SSH key for main server)" -ForegroundColor White
Write-Host "- D:\VideoTranscode\scripts\upload_to_main.ps1" -ForegroundColor White
Write-Host "- D:\VideoTranscode\scripts\watcher.ps1 (with auto-upload)" -ForegroundColor White
Write-Host ""
Write-Host "Next: Test the complete workflow" -ForegroundColor Yellow
Write-Host ""
