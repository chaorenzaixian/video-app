# 深度网络测试脚本
# 测试多个方面的网络性能

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "深度网络性能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试结果数组
$results = @()

# 1. 测试多个地区的下载速度
Write-Host "[1/8] 测试全球多个下载源..." -ForegroundColor Yellow
Write-Host ""

$sources = @(
    @{Name="欧洲-瑞典-Tele2"; Url="http://speedtest.tele2.net/10MB.zip"; Size=10},
    @{Name="欧洲-英国-ThinkBroadband"; Url="http://ipv4.download.thinkbroadband.com/10MB.zip"; Size=10},
    @{Name="欧洲-法国-OVH"; Url="http://proof.ovh.net/files/10Mb.dat"; Size=10},
    @{Name="欧洲-德国-Hetzner"; Url="http://speed.hetzner.de/10MB.bin"; Size=10},
    @{Name="亚洲-新加坡-Linode"; Url="http://speedtest.singapore.linode.com/100MB-singapore.bin"; Size=100},
    @{Name="美国-纽约-Linode"; Url="http://speedtest.newark.linode.com/100MB-newark.bin"; Size=100}
)

foreach ($source in $sources) {
    Write-Host "  测试: $($source.Name)" -ForegroundColor White
    try {
        $output = "C:\test_$($source.Name -replace '[^a-zA-Z0-9]','_').tmp"
        $startTime = Get-Date
        Invoke-WebRequest -Uri $source.Url -OutFile $output -UseBasicParsing -TimeoutSec 60
        $endTime = Get-Date
        
        $duration = ($endTime - $startTime).TotalSeconds
        $fileSize = (Get-Item $output).Length / 1MB
        $speed = $fileSize / $duration
        $bandwidth = $speed * 8
        
        $result = @{
            Source = $source.Name
            Speed = [math]::Round($speed, 2)
            Bandwidth = [math]::Round($bandwidth, 2)
            Duration = [math]::Round($duration, 2)
            Size = $fileSize
        }
        $results += $result
        
        Write-Host "    速度: $($result.Speed) MB/s ($($result.Bandwidth) Mbps)" -ForegroundColor Green
        Write-Host "    耗时: $($result.Duration) 秒" -ForegroundColor Gray
        
        Remove-Item $output -Force
    } catch {
        Write-Host "    失败: $_" -ForegroundColor Red
        $results += @{Source=$source.Name; Speed=0; Bandwidth=0; Duration=0; Size=0}
    }
    Write-Host ""
}

# 2. 测试并发下载
Write-Host "[2/8] 测试并发下载性能..." -ForegroundColor Yellow
Write-Host ""

$concurrentUrl = "http://speedtest.tele2.net/10MB.zip"
$jobs = @()

Write-Host "  启动3个并发下载..." -ForegroundColor White
$concurrentStart = Get-Date

for ($i = 1; $i -le 3; $i++) {
    $job = Start-Job -ScriptBlock {
        param($url, $output)
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    } -ArgumentList $concurrentUrl, "C:\concurrent_$i.tmp"
    $jobs += $job
}

Wait-Job $jobs | Out-Null
$concurrentEnd = Get-Date
$concurrentDuration = ($concurrentEnd - $concurrentStart).TotalSeconds

$totalSize = 0
foreach ($i in 1..3) {
    if (Test-Path "C:\concurrent_$i.tmp") {
        $totalSize += (Get-Item "C:\concurrent_$i.tmp").Length
        Remove-Item "C:\concurrent_$i.tmp" -Force
    }
}

$concurrentSpeed = ($totalSize / 1MB) / $concurrentDuration
Write-Host "  并发总速度: $([math]::Round($concurrentSpeed, 2)) MB/s" -ForegroundColor Green
Write-Host "  总耗时: $([math]::Round($concurrentDuration, 2)) 秒" -ForegroundColor Gray
Write-Host ""

Remove-Job $jobs -Force

# 3. 测试上传速度
Write-Host "[3/8] 测试上传速度..." -ForegroundColor Yellow
Write-Host ""

# 创建测试文件
$testFile = "C:\upload_test.dat"
$testData = New-Object byte[] (10MB)
(New-Object Random).NextBytes($testData)
[System.IO.File]::WriteAllBytes($testFile, $testData)

try {
    Write-Host "  上传到主服务器 (38.47.218.137)..." -ForegroundColor White
    $uploadStart = Get-Date
    
    # 使用curl上传
    $curlResult = & curl.exe -X POST -F "file=@$testFile" http://38.47.218.137/upload -w "%{speed_upload}" -o NUL 2>&1
    
    $uploadEnd = Get-Date
    $uploadDuration = ($uploadEnd - $uploadStart).TotalSeconds
    $uploadSpeed = 10 / $uploadDuration
    
    Write-Host "  上传速度: $([math]::Round($uploadSpeed, 2)) MB/s" -ForegroundColor Green
} catch {
    Write-Host "  上传测试失败: $_" -ForegroundColor Red
}

Remove-Item $testFile -Force -ErrorAction SilentlyContinue
Write-Host ""

# 4. 测试DNS解析速度
Write-Host "[4/8] 测试DNS解析..." -ForegroundColor Yellow
Write-Host ""

$dnsTests = @("google.com", "cloudflare.com", "github.com", "telegram.org")
foreach ($domain in $dnsTests) {
    $dnsStart = Get-Date
    $dnsResult = Resolve-DnsName $domain -ErrorAction SilentlyContinue
    $dnsEnd = Get-Date
    $dnsDuration = ($dnsEnd - $dnsStart).TotalMilliseconds
    
    if ($dnsResult) {
        Write-Host "  $domain : $([math]::Round($dnsDuration, 2)) ms" -ForegroundColor Green
    } else {
        Write-Host "  $domain : 失败" -ForegroundColor Red
    }
}
Write-Host ""

# 5. 测试到关键服务器的延迟
Write-Host "[5/8] 测试网络延迟..." -ForegroundColor Yellow
Write-Host ""

$pingTargets = @(
    @{Name="主服务器(香港)"; IP="38.47.218.137"},
    @{Name="Google DNS"; IP="8.8.8.8"},
    @{Name="Cloudflare DNS"; IP="1.1.1.1"},
    @{Name="本地网关"; IP="198.176.60.254"}
)

foreach ($target in $pingTargets) {
    $pingResult = Test-Connection -ComputerName $target.IP -Count 4 -ErrorAction SilentlyContinue
    if ($pingResult) {
        $avgLatency = ($pingResult | Measure-Object -Property ResponseTime -Average).Average
        $minLatency = ($pingResult | Measure-Object -Property ResponseTime -Minimum).Minimum
        $maxLatency = ($pingResult | Measure-Object -Property ResponseTime -Maximum).Maximum
        Write-Host "  $($target.Name) ($($target.IP)):" -ForegroundColor White
        Write-Host "    平均: $([math]::Round($avgLatency, 2)) ms | 最小: $minLatency ms | 最大: $maxLatency ms" -ForegroundColor Green
    } else {
        Write-Host "  $($target.Name): 无法连接" -ForegroundColor Red
    }
}
Write-Host ""

# 6. 测试MTU和包大小
Write-Host "[6/8] 测试MTU和数据包..." -ForegroundColor Yellow
Write-Host ""

$mtuSizes = @(1500, 1400, 1300, 1200)
foreach ($mtu in $mtuSizes) {
    $pingResult = ping -n 1 -l $mtu -f 8.8.8.8 2>&1
    if ($pingResult -match "TTL=") {
        Write-Host "  MTU $mtu : 通过" -ForegroundColor Green
    } else {
        Write-Host "  MTU $mtu : 失败 (需要分片)" -ForegroundColor Yellow
    }
}
Write-Host ""

# 7. 检查网络限制和QoS
Write-Host "[7/8] 检查网络配置..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  TCP全局设置:" -ForegroundColor White
netsh interface tcp show global | Select-String "接收窗口自动调谐级别|RSS 状态|Chimney 卸载状态"

Write-Host ""
Write-Host "  网络适配器状态:" -ForegroundColor White
Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | ForEach-Object {
    Write-Host "    $($_.Name): $($_.LinkSpeed)" -ForegroundColor Green
}

Write-Host ""
Write-Host "  代理设置:" -ForegroundColor White
$proxySettings = netsh winhttp show proxy
if ($proxySettings -match "直接访问") {
    Write-Host "    无代理 (直接访问)" -ForegroundColor Green
} else {
    Write-Host "    $proxySettings" -ForegroundColor Yellow
}
Write-Host ""

# 8. 测试持续下载稳定性
Write-Host "[8/8] 测试持续下载稳定性..." -ForegroundColor Yellow
Write-Host ""

Write-Host "  下载100MB文件测试稳定性..." -ForegroundColor White
try {
    $stableUrl = "http://speedtest.tele2.net/100MB.zip"
    $stableOutput = "C:\stable_test.zip"
    
    $stableStart = Get-Date
    Invoke-WebRequest -Uri $stableUrl -OutFile $stableOutput -UseBasicParsing -TimeoutSec 300
    $stableEnd = Get-Date
    
    $stableDuration = ($stableEnd - $stableStart).TotalSeconds
    $stableSize = (Get-Item $stableOutput).Length / 1MB
    $stableSpeed = $stableSize / $stableDuration
    
    Write-Host "  大文件下载速度: $([math]::Round($stableSpeed, 2)) MB/s" -ForegroundColor Green
    Write-Host "  总耗时: $([math]::Round($stableDuration, 2)) 秒" -ForegroundColor Gray
    
    Remove-Item $stableOutput -Force
} catch {
    Write-Host "  大文件下载失败: $_" -ForegroundColor Red
}
Write-Host ""

# 生成报告
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "测试结果汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "下载速度测试结果:" -ForegroundColor Yellow
$results | ForEach-Object {
    if ($_.Speed -gt 0) {
        Write-Host "  $($_.Source): $($_.Speed) MB/s ($($_.Bandwidth) Mbps)" -ForegroundColor White
    }
}

Write-Host ""
$avgSpeed = ($results | Where-Object {$_.Speed -gt 0} | Measure-Object -Property Speed -Average).Average
$maxSpeed = ($results | Where-Object {$_.Speed -gt 0} | Measure-Object -Property Speed -Maximum).Maximum
$minSpeed = ($results | Where-Object {$_.Speed -gt 0} | Measure-Object -Property Speed -Minimum).Minimum

Write-Host "统计数据:" -ForegroundColor Yellow
Write-Host "  平均速度: $([math]::Round($avgSpeed, 2)) MB/s" -ForegroundColor White
Write-Host "  最快速度: $([math]::Round($maxSpeed, 2)) MB/s" -ForegroundColor Green
Write-Host "  最慢速度: $([math]::Round($minSpeed, 2)) MB/s" -ForegroundColor Red
Write-Host ""

# 诊断建议
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断建议" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($avgSpeed -lt 5) {
    Write-Host "⚠ 网络速度严重不足！" -ForegroundColor Red
    Write-Host "  建议:" -ForegroundColor Yellow
    Write-Host "  1. 联系服务器提供商检查带宽限制" -ForegroundColor White
    Write-Host "  2. 询问是否为共享带宽" -ForegroundColor White
    Write-Host "  3. 考虑升级到更高带宽套餐" -ForegroundColor White
    Write-Host "  4. 或更换服务器提供商" -ForegroundColor White
} elseif ($avgSpeed -lt 20) {
    Write-Host "⚠ 网络速度偏低" -ForegroundColor Yellow
    Write-Host "  建议优化网络配置或考虑升级带宽" -ForegroundColor White
} else {
    Write-Host "✓ 网络速度正常" -ForegroundColor Green
}

Write-Host ""
Write-Host "测试完成！" -ForegroundColor Green
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
