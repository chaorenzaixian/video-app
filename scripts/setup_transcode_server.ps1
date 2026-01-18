# Windows Server 转码服务器一键配置脚本
# 使用方法：在服务器上以管理员身份运行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  视频转码服务器自动配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "错误：请以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host "右键点击脚本 -> 以管理员身份运行" -ForegroundColor Yellow
    pause
    exit
}

Write-Host "[1/8] 配置系统设置..." -ForegroundColor Green

# 设置时区
Set-TimeZone -Id "China Standard Time" -ErrorAction SilentlyContinue

# 关闭 Windows Defender 实时保护（提升性能）
Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue

# 禁用 Windows Update 自动更新
Stop-Service wuauserv -ErrorAction SilentlyContinue
Set-Service wuauserv -StartupType Disabled -ErrorAction SilentlyContinue

Write-Host "✓ 系统设置完成" -ForegroundColor Green
Write-Host ""

Write-Host "[2/8] 安装 Chocolatey 包管理器..." -ForegroundColor Green

# 安装 Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
try {
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-Host "✓ Chocolatey 安装完成" -ForegroundColor Green
} catch {
    Write-Host "✗ Chocolatey 安装失败，请检查网络" -ForegroundColor Red
}
Write-Host ""

Write-Host "[3/8] 安装必要软件..." -ForegroundColor Green

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 安装软件
choco install ffmpeg -y
choco install python -y
choco install git -y
choco install 7zip -y

Write-Host "✓ 软件安装完成" -ForegroundColor Green
Write-Host ""

Write-Host "[4/8] 创建工作目录..." -ForegroundColor Green

# 创建目录结构
$workDir = "C:\VideoTranscode"
New-Item -ItemType Directory -Path "$workDir" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\downloads" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\processing" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\completed" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\scripts" -Force | Out-Null

Write-Host "✓ 工作目录创建完成: $workDir" -ForegroundColor Green
Write-Host ""

Write-Host "[5/8] 安装 Python 依赖..." -ForegroundColor Green

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 安装 Python 包
python -m pip install --upgrade pip
pip install watchdog requests

Write-Host "✓ Python 依赖安装完成" -ForegroundColor Green
Write-Host ""

Write-Host "[6/8] 创建转码脚本..." -ForegroundColor Green

# 创建转码脚本
$transcodeScript = @'
# transcode.ps1 - 视频转码脚本
param(
    [string]$InputFile,
    [string]$OutputDir = "C:\VideoTranscode\completed"
)

$videoId = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
$outputPath = Join-Path $OutputDir "$videoId"
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

Write-Host "开始转码: $InputFile"

# HLS 转码
$hlsDir = Join-Path $outputPath "hls"
New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null

ffmpeg -i $InputFile `
    -c:v libx264 -preset fast -crf 22 `
    -c:a aac -b:a 128k `
    -hls_time 10 -hls_list_size 0 `
    -hls_segment_filename "$hlsDir\segment_%03d.ts" `
    "$hlsDir\playlist.m3u8"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 转码完成: $videoId" -ForegroundColor Green
    
    # 生成缩略图
    $thumbPath = Join-Path $outputPath "thumbnail.jpg"
    ffmpeg -i $InputFile -ss 00:00:03 -vframes 1 -vf "scale=640:-1" $thumbPath -y
    
    return $true
} else {
    Write-Host "✗ 转码失败: $videoId" -ForegroundColor Red
    return $false
}
'@

Set-Content -Path "$workDir\scripts\transcode.ps1" -Value $transcodeScript -Encoding UTF8

Write-Host "✓ 转码脚本创建完成" -ForegroundColor Green
Write-Host ""

Write-Host "[7/8] 创建监控服务..." -ForegroundColor Green

# 创建监控脚本
$watcherScript = @'
# watcher.py - 文件监控服务
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = r"C:\VideoTranscode\downloads"
PROCESSING_DIR = r"C:\VideoTranscode\processing"
SCRIPT_PATH = r"C:\VideoTranscode\scripts\transcode.ps1"

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if not file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm')):
            return
        
        print(f"检测到新视频: {file_path}")
        
        # 等待文件写入完成
        time.sleep(2)
        
        # 移动到处理目录
        filename = os.path.basename(file_path)
        processing_path = os.path.join(PROCESSING_DIR, filename)
        
        try:
            os.rename(file_path, processing_path)
            print(f"开始处理: {filename}")
            
            # 调用转码脚本
            subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass",
                "-File", SCRIPT_PATH,
                "-InputFile", processing_path
            ])
            
        except Exception as e:
            print(f"处理失败: {e}")

if __name__ == "__main__":
    print("视频监控服务启动...")
    print(f"监控目录: {WATCH_DIR}")
    
    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(PROCESSING_DIR, exist_ok=True)
    
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
'@

Set-Content -Path "$workDir\scripts\watcher.py" -Value $watcherScript -Encoding UTF8

Write-Host "✓ 监控服务创建完成" -ForegroundColor Green
Write-Host ""

Write-Host "[8/8] 创建启动脚本..." -ForegroundColor Green

# 创建启动脚本
$startScript = @'
@echo off
title 视频转码监控服务
cd /d C:\VideoTranscode
python scripts\watcher.py
pause
'@

Set-Content -Path "$workDir\start_service.bat" -Value $startScript -Encoding ASCII

# 创建桌面快捷方式
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\启动转码服务.lnk")
$Shortcut.TargetPath = "$workDir\start_service.bat"
$Shortcut.WorkingDirectory = $workDir
$Shortcut.Save()

Write-Host "✓ 启动脚本创建完成" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 手动安装 Telegram Desktop: https://desktop.telegram.org/" -ForegroundColor White
Write-Host "2. 手动安装 Chrome: https://www.google.com/chrome/" -ForegroundColor White
Write-Host "3. 双击桌面上的 '启动转码服务' 快捷方式" -ForegroundColor White
Write-Host "4. 将视频文件放入: C:\VideoTranscode\downloads" -ForegroundColor White
Write-Host ""
Write-Host "转码后的文件位置: C:\VideoTranscode\completed" -ForegroundColor Cyan
Write-Host ""

pause
