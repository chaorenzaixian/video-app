# Windows 服务器远程连接和配置脚本
# 使用 plink (PuTTY) 进行自动化连接

$serverIP = "198.176.60.121"
$username = "Administrator"
$password = "jCkMIjNlnSd7f6GM"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows 转码服务器配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否安装了 plink
$plinkPath = "C:\Program Files\PuTTY\plink.exe"
if (-not (Test-Path $plinkPath)) {
    Write-Host "未找到 plink，正在安装 PuTTY..." -ForegroundColor Yellow
    
    # 下载 PuTTY
    $puttyUrl = "https://the.earth.li/~sgtatham/putty/latest/w64/putty-64bit-0.81-installer.msi"
    $puttyInstaller = "$env:TEMP\putty-installer.msi"
    
    try {
        Invoke-WebRequest -Uri $puttyUrl -OutFile $puttyInstaller -UseBasicParsing
        Start-Process msiexec.exe -ArgumentList "/i `"$puttyInstaller`" /quiet /norestart" -Wait
        Write-Host "PuTTY 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "安装失败: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "请手动安装 PuTTY: https://www.putty.org/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "正在连接到服务器 $serverIP ..." -ForegroundColor Yellow
Write-Host ""

# 使用 plink 执行命令
$commands = @"
echo ======================================== && `
echo 服务器信息 && `
echo ======================================== && `
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" && `
echo. && `
echo ======================================== && `
echo 磁盘空间 && `
echo ======================================== && `
wmic logicaldisk get caption,freespace,size && `
echo. && `
echo ======================================== && `
echo 网络配置 && `
echo ======================================== && `
ipconfig | findstr IPv4 && `
echo. && `
echo 连接成功！
"@

# 执行远程命令
& $plinkPath -ssh $username@$serverIP -pw $password -batch $commands

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "连接测试完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
