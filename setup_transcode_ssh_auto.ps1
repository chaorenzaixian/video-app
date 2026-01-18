# Auto setup SSH key authentication on transcode server
$server = "198.176.60.121"
$user = "Administrator"
$pass = "jCkMIjNlnSd7f6GM"
$publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIET29AuLWcZ9YFVpwDKYl38HpN5JWrop5jFkEJ3nsv2A root@HB131103"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup SSH Key Authentication" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Creating .ssh directory..." -ForegroundColor Yellow
$cmd1 = "mkdir C:\Users\Administrator\.ssh -Force"
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} "powershell -Command `"$cmd1`""

Write-Host "Step 2: Adding public key..." -ForegroundColor Yellow
$cmd2 = "echo $publicKey > C:\Users\Administrator\.ssh\authorized_keys"
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} $cmd2

Write-Host "Step 3: Setting permissions..." -ForegroundColor Yellow
$cmd3 = "icacls C:\Users\Administrator\.ssh\authorized_keys /inheritance:r ; icacls C:\Users\Administrator\.ssh\authorized_keys /grant:r `"Administrator:F`""
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} "powershell -Command `"$cmd3`""

Write-Host "Step 4: Restarting SSH service..." -ForegroundColor Yellow
$cmd4 = "Restart-Service sshd"
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} "powershell -Command `"$cmd4`""

Write-Host ""
Write-Host "Step 5: Testing key authentication..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
ssh -i server_key_new -o StrictHostKeyChecking=no ${user}@${server} "echo SSH key authentication successful!"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SSH Key Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now connect without password:" -ForegroundColor Cyan
    Write-Host "ssh -i server_key_new Administrator@198.176.60.121" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Setup may have failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Please check the steps manually" -ForegroundColor Yellow
}
