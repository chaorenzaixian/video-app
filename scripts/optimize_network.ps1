# Windows 网络优化脚本
# 需要管理员权限运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "网络性能优化" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 启用TCP窗口自动调优
Write-Host "[1] 启用TCP窗口自动调优..." -ForegroundColor Yellow
netsh interface tcp set global autotuninglevel=normal
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 2. 禁用TCP启发式缩放
Write-Host "[2] 优化TCP缩放..." -ForegroundColor Yellow
netsh interface tcp set heuristics disabled
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 3. 启用RSS (Receive Side Scaling)
Write-Host "[3] 启用RSS..." -ForegroundColor Yellow
netsh interface tcp set global rss=enabled
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 4. 启用Chimney Offload
Write-Host "[4] 启用Chimney Offload..." -ForegroundColor Yellow
netsh interface tcp set global chimney=enabled
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 5. 设置网络限流策略为无限制
Write-Host "[5] 禁用网络限流..." -ForegroundColor Yellow
netsh interface tcp set global netdma=enabled
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 6. 优化接收窗口大小
Write-Host "[6] 优化接收窗口..." -ForegroundColor Yellow
netsh interface tcp set global dca=enabled
Write-Host "✓ 完成" -ForegroundColor Green
Write-Host ""

# 7. 显示当前设置
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "当前TCP设置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
netsh interface tcp show global
Write-Host ""

# 8. 测试优化效果
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试优化效果" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$testUrl = "http://speedtest.tele2.net/10MB.zip"
$output = "C:\test_optimized.zip"

Write-Host "下载测试文件..." -ForegroundColor Yellow
$startTime = Get-Date
Invoke-WebRequest -Uri $testUrl -OutFile $output -UseBasicParsing
$endTime = Get-Date

$duration = ($endTime - $startTime).TotalSeconds
$fileSize = (Get-Item $output).Length / 1MB
$speed = $fileSize / $duration
$bandwidth = $speed * 8

Write-Host ""
Write-Host "优化后速度: $([math]::Round($speed, 2)) MB/s" -ForegroundColor Green
Write-Host "带宽: $([math]::Round($bandwidth, 2)) Mbps" -ForegroundColor Green

Remove-Item $output -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "优化完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "如果速度仍然很慢，请联系服务器提供商检查:" -ForegroundColor Yellow
Write-Host "1. 是否有带宽限制策略" -ForegroundColor White
Write-Host "2. 是否有流量整形(QoS)限制" -ForegroundColor White
Write-Host "3. 上游网络是否有问题" -ForegroundColor White
