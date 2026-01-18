@echo off
echo ========================================
echo 快速网络测试
echo ========================================
echo.

echo [1] 测试 Hetzner (德国)
powershell -Command "$s=Get-Date; curl -o C:\t1.tmp http://speed.hetzner.de/10MB.bin; $e=Get-Date; $d=($e-$s).TotalSeconds; $sz=(Get-Item C:\t1.tmp).Length/1MB; Write-Host 'Speed:' ($sz/$d) 'MB/s'; Remove-Item C:\t1.tmp"
echo.

echo [2] 测试 OVH (法国)
powershell -Command "$s=Get-Date; curl -o C:\t2.tmp http://proof.ovh.net/files/10Mb.dat; $e=Get-Date; $d=($e-$s).TotalSeconds; $sz=(Get-Item C:\t2.tmp).Length/1MB; Write-Host 'Speed:' ($sz/$d) 'MB/s'; Remove-Item C:\t2.tmp"
echo.

echo [3] 测试 Tele2 (瑞典)
powershell -Command "$s=Get-Date; curl -o C:\t3.tmp http://speedtest.tele2.net/10MB.zip; $e=Get-Date; $d=($e-$s).TotalSeconds; $sz=(Get-Item C:\t3.tmp).Length/1MB; Write-Host 'Speed:' ($sz/$d) 'MB/s'; Remove-Item C:\t3.tmp"
echo.

echo [4] 测试网络延迟
ping -n 4 38.47.218.137
echo.
ping -n 4 8.8.8.8
echo.

echo [5] 测试DNS
nslookup google.com
echo.

echo [6] 检查网络适配器
wmic nic where NetEnabled=true get Name,Speed
echo.

echo [7] TCP设置
netsh interface tcp show global
echo.

echo ========================================
echo 测试完成
echo ========================================
pause
