# Windows 服务器下载速度测试脚本
# 使用方法: 在服务器上运行 powershell -ExecutionPolicy Bypass -File test_download_speed.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始测试下载速度..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试文件 URL (100MB 测试文件)
$testUrl = "http://speedtest.tele2.net/100MB.zip"
$output = "$env:TEMP\speedtest_100mb.zip"

try {
    # 清理旧文件
    if (Test-Path $output) {
        Remove-Item $output -Force
    }

    Write-Host "测试文件: 100MB" -ForegroundColor White
    Write-Host "下载地址: $testUrl" -ForegroundColor White
    Write-Host ""
    Write-Host "开始下载..." -ForegroundColor Yellow
    
    # 记录开始时间
    $startTime = Get-Date
    
    # 下载文件
    Invoke-WebRequest -Uri $testUrl -OutFile $output -UseBasicParsing
    
    # 记录结束时间
    $endTime = Get-Date
    
    # 计算统计数据
    $duration = ($endTime - $startTime).TotalSeconds
    $fileSize = (Get-Item $output).Length / 1MB
    $speed = $fileSize / $duration
    $bandwidth = $speed * 8
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "下载完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
    Write-Host "耗时: $([math]::Round($duration, 2)) 秒" -ForegroundColor White
    Write-Host "平均速度: $([math]::Round($speed, 2)) MB/s" -ForegroundColor Yellow
    Write-Host "带宽: $([math]::Round($bandwidth, 2)) Mbps" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # 评估结果
    if ($bandwidth -gt 150) {
        Write-Host "✓ 网络速度优秀！适合大量视频下载和转码" -ForegroundColor Green
    } elseif ($bandwidth -gt 80) {
        Write-Host "✓ 网络速度良好，可以满足转码需求" -ForegroundColor Green
    } elseif ($bandwidth -gt 40) {
        Write-Host "⚠ 网络速度一般，建议优化下载策略" -ForegroundColor Yellow
    } else {
        Write-Host "✗ 网络速度较慢，可能影响转码效率" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "预估性能:" -ForegroundColor Cyan
    $downloadTime1GB = 1024 / $speed
    Write-Host "- 下载 1GB 视频需要: $([math]::Round($downloadTime1GB, 1)) 秒 ($([math]::Round($downloadTime1GB/60, 1)) 分钟)" -ForegroundColor White
    
    # 清理测试文件
    Remove-Item $output -Force
    Write-Host ""
    Write-Host "测试文件已清理" -ForegroundColor Gray
    
} catch {
    Write-Host ""
    Write-Host "下载测试失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 网络连接问题" -ForegroundColor White
    Write-Host "2. 防火墙阻止" -ForegroundColor White
    Write-Host "3. 测试服务器不可用" -ForegroundColor White
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
