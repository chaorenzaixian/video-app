# 网络诊断脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "网络诊断工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 网络适配器信息
Write-Host "[1] 网络适配器信息" -ForegroundColor Yellow
Get-NetAdapter | Select-Object Name, Status, LinkSpeed | Format-Table -AutoSize
Write-Host ""

# 2. IP配置
Write-Host "[2] IP配置" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"} | Select-Object InterfaceAlias, IPAddress | Format-Table -AutoSize
Write-Host ""

# 3. 测试到主服务器的连接
Write-Host "[3] 测试到主服务器 (38.47.218.137)" -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName 38.47.218.137 -Count 4 -ErrorAction SilentlyContinue
if ($pingResult) {
    $avgLatency = ($pingResult | Measure-Object -Property ResponseTime -Average).Average
    Write-Host "平均延迟: $([math]::Round($avgLatency, 2)) ms" -ForegroundColor Green
} else {
    Write-Host "无法连接到主服务器" -ForegroundColor Red
}
Write-Host ""

# 4. 测试多个下载源
Write-Host "[4] 测试下载速度" -ForegroundColor Yellow

$testSources = @(
    @{Name="欧洲-Tele2"; Url="http://speedtest.tele2.net/10MB.zip"},
    @{Name="英国-ThinkBroadband"; Url="http://ipv4.download.thinkbroadband.com/10MB.zip"},
    @{Name="法国-OVH"; Url="http://proof.ovh.net/files/10Mb.dat"}
)

foreach ($source in $testSources) {
    Write-Host "  测试 $($source.Name)..." -ForegroundColor White
    try {
        $output = "C:\test_$($source.Name).tmp"
        $startTime = Get-Date
        Invoke-WebRequest -Uri $source.Url -OutFile $output -UseBasicParsing -TimeoutSec 30
        $endTime = Get-Date
        
        $duration = ($endTime - $startTime).TotalSeconds
        $fileSize = (Get-Item $output).Length / 1MB
        $speed = $fileSize / $duration
        $bandwidth = $speed * 8
        
        Write-Host "    速度: $([math]::Round($speed, 2)) MB/s ($([math]::Round($bandwidth, 2)) Mbps)" -ForegroundColor Green
        Remove-Item $output -Force
    } catch {
        Write-Host "    失败: $_" -ForegroundColor Red
    }
}
Write-Host ""

# 5. DNS测试
Write-Host "[5] DNS解析测试" -ForegroundColor Yellow
$dnsTest = Resolve-DnsName google.com -ErrorAction SilentlyContinue
if ($dnsTest) {
    Write-Host "DNS工作正常" -ForegroundColor Green
} else {
    Write-Host "DNS解析失败" -ForegroundColor Red
}
Write-Host ""

# 6. 路由追踪到主服务器
Write-Host "[6] 路由追踪到主服务器" -ForegroundColor Yellow
Write-Host "执行 tracert 38.47.218.137 (可能需要1-2分钟)..." -ForegroundColor Gray
$tracert = tracert -d -h 15 38.47.218.137
$tracert | Select-Object -First 20
Write-Host ""

# 7. 检查防火墙和代理
Write-Host "[7] 检查系统配置" -ForegroundColor Yellow
$proxy = netsh winhttp show proxy
Write-Host "代理配置:"
$proxy
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果下载速度持续很慢，可能的原因:" -ForegroundColor Yellow
Write-Host "1. 服务器提供商限速" -ForegroundColor White
Write-Host "2. 网络拥堵或路由问题" -ForegroundColor White
Write-Host "3. 防火墙或安全软件限制" -ForegroundColor White
Write-Host "4. 服务器端口限制" -ForegroundColor White
Write-Host ""
Write-Host "建议联系服务器提供商检查带宽限制" -ForegroundColor Cyan
