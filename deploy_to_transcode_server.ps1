# Deploy upload feature to transcode server
$server = "198.176.60.121"
$user = "Administrator"
$pass = "jCkMIjNlnSd7f6GM"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying Upload Feature" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Files to deploy
$files = @(
    @{Local="deploy_files\upload_simple.py"; Remote="D:/VideoTranscode/scripts/upload_simple.py"},
    @{Local="deploy_files\upload_to_main.ps1"; Remote="D:/VideoTranscode/scripts/upload_to_main.ps1"},
    @{Local="deploy_files\watcher.ps1"; Remote="D:/VideoTranscode/scripts/watcher.ps1"}
)

Write-Host "Step 1: Installing paramiko on transcode server..." -ForegroundColor Yellow
$cmd = "python -m pip install paramiko"
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} $cmd

Write-Host ""
Write-Host "Step 2: Uploading files..." -ForegroundColor Yellow

foreach ($file in $files) {
    Write-Host "  Uploading $($file.Local)..." -ForegroundColor Gray
    
    # Use scp with password via sshpass or manual
    $localPath = $file.Local
    $remotePath = "${user}@${server}:$($file.Remote)"
    
    # Try using scp (may prompt for password)
    scp -o StrictHostKeyChecking=no $localPath $remotePath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Success" -ForegroundColor Green
    } else {
        Write-Host "    Failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Step 3: Testing upload..." -ForegroundColor Yellow
$testCmd = "python D:\VideoTranscode\scripts\upload_simple.py D:\VideoTranscode\completed\test2_transcoded.mp4"
echo $pass | ssh -o StrictHostKeyChecking=no ${user}@${server} $testCmd

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
