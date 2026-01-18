# Setup SSH key on transcode server
$transcodeServer = "198.176.60.121"
$transcodeUser = "Administrator"
$transcodePass = "jCkMIjNlnSd7f6GM"
$keyContent = @"
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----
"@

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup SSH Key on Transcode Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create key file locally first
$localKeyFile = "C:\temp_server_key"
$keyContent | Out-File -FilePath $localKeyFile -Encoding ASCII -NoNewline

Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
try {
    $testCmd = "echo Connection test successful"
    $result = echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${transcodeUser}@${transcodeServer} $testCmd 2>&1
    Write-Host "SSH connection OK" -ForegroundColor Green
} catch {
    Write-Host "SSH connection failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Creating key file on remote server..." -ForegroundColor Yellow

# Use scp to copy the key file
try {
    echo y | C:\Windows\System32\OpenSSH\scp.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $localKeyFile ${transcodeUser}@${transcodeServer}:C:\server_key 2>&1
    Write-Host "Key file uploaded successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to upload key file: $_" -ForegroundColor Red
    exit 1
}

# Clean up local temp file
Remove-Item $localKeyFile -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Step 3: Verifying key file on remote server..." -ForegroundColor Yellow
$verifyCmd = "Test-Path C:\server_key"
$result = echo y | C:\Windows\System32\OpenSSH\ssh.exe -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL ${transcodeUser}@${transcodeServer} "powershell -Command `"$verifyCmd`"" 2>&1

if ($result -match "True") {
    Write-Host "Key file verified successfully" -ForegroundColor Green
} else {
    Write-Host "Key file verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SSH Key Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Key file location: C:\server_key" -ForegroundColor White
Write-Host "Now you can test the upload script" -ForegroundColor White
Write-Host ""
