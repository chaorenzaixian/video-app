# 远程服务器安装脚本
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

# 安装 Chocolatey
Write-Host "安装 Chocolatey..." -ForegroundColor Yellow
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Chocolatey 安装完成" -ForegroundColor Green

# 安装软件
Write-Host "安装 Chrome 和 Telegram..." -ForegroundColor Yellow
choco install googlechrome telegram -y

Write-Host "所有软件安装完成！" -ForegroundColor Green
