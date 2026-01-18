# watcher.ps1 - 视频转码监控服务
$watchFolder = "C:\VideoTranscode\downloads"
$processingFolder = "C:\VideoTranscode\processing"
$completedFolder = "C:\VideoTranscode\completed"
$logFile = "C:\VideoTranscode\logs\watcher.log"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
    Write-Host "$timestamp - $Message"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频转码监控服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "监控目录: $watchFolder" -ForegroundColor White
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

Write-Log "监控服务启动"

$processedCount = 0

while ($true) {
    try {
        $videos = Get-ChildItem -Path $watchFolder -Include *.mp4,*.avi,*.mov,*.mkv -ErrorAction SilentlyContinue
        
        foreach ($video in $videos) {
            Write-Log "发现视频: $($video.Name)"
            
            $processingPath = Join-Path $processingFolder $video.Name
            Move-Item -Path $video.FullName -Destination $processingPath -Force
            
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name)
            $outputName = "${baseName}_transcoded.mp4"
            $outputPath = Join-Path $completedFolder $outputName
            
            Write-Log "开始转码..."
            & "C:\VideoTranscode\scripts\transcode.ps1" -InputFile $processingPath -OutputFile $outputPath
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "转码成功: $outputName"
                $processedCount++
                Remove-Item -Path $processingPath -Force
            } else {
                Write-Log "转码失败"
            }
        }
        
        Start-Sleep -Seconds 10
    } catch {
        Write-Log "异常: $_"
        Start-Sleep -Seconds 30
    }
}
