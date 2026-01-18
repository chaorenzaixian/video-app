# Windows 转码服务器一键配置脚本
# 在服务器本地运行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频转码服务器配置向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 安装 Chrome 和 Telegram
Write-Host "[1/6] 安装必要软件..." -ForegroundColor Yellow
Write-Host "正在安装 Google Chrome..." -ForegroundColor White
choco install googlechrome -y

Write-Host "正在安装 Telegram Desktop..." -ForegroundColor White
choco install telegram -y

Write-Host "✓ 软件安装完成" -ForegroundColor Green
Write-Host ""

# 2. 测试网络速度
Write-Host "[2/6] 测试网络速度..." -ForegroundColor Yellow
$testUrl = "http://speedtest.tele2.net/10MB.zip"
$output = "$env:TEMP\speedtest.zip"

try {
    $startTime = Get-Date
    Invoke-WebRequest -Uri $testUrl -OutFile $output -UseBasicParsing
    $endTime = Get-Date
    
    $duration = ($endTime - $startTime).TotalSeconds
    $fileSize = (Get-Item $output).Length / 1MB
    $speed = $fileSize / $duration
    $bandwidth = $speed * 8
    
    Write-Host "下载速度: $([math]::Round($speed, 2)) MB/s" -ForegroundColor Green
    Write-Host "带宽: $([math]::Round($bandwidth, 2)) Mbps" -ForegroundColor Green
    
    Remove-Item $output -Force
} catch {
    Write-Host "网络测试失败，继续配置..." -ForegroundColor Yellow
}
Write-Host ""

# 3. 创建工作目录
Write-Host "[3/6] 创建工作目录..." -ForegroundColor Yellow
$workDir = "C:\VideoTranscode"
$dirs = @("downloads", "processing", "completed", "logs", "scripts")

foreach ($dir in $dirs) {
    $path = Join-Path $workDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}
Write-Host "✓ 目录创建完成: $workDir" -ForegroundColor Green
Write-Host ""

# 4. 创建转码脚本
Write-Host "[4/6] 创建转码脚本..." -ForegroundColor Yellow

$transcodeScript = @'
# 视频转码脚本
param(
    [string]$InputFile,
    [string]$OutputFile
)

$ffmpegPath = "ffmpeg"
$logFile = "C:\VideoTranscode\logs\transcode_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "开始转码: $InputFile" -ForegroundColor Yellow

$arguments = @(
    "-i", $InputFile,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    "-y",
    $OutputFile
)

$process = Start-Process -FilePath $ffmpegPath -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $logFile

if ($process.ExitCode -eq 0) {
    Write-Host "✓ 转码完成: $OutputFile" -ForegroundColor Green
    return $true
} else {
    Write-Host "✗ 转码失败，查看日志: $logFile" -ForegroundColor Red
    return $false
}
'@

$transcodeScript | Out-File -FilePath "$workDir\scripts\transcode.ps1" -Encoding UTF8
Write-Host "✓ 转码脚本已创建" -ForegroundColor Green
Write-Host ""

# 5. 创建监控服务脚本
Write-Host "[5/6] 创建监控服务..." -ForegroundColor Yellow

$watcherScript = @'
# 视频转码监控服务
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

Write-Log "监控服务启动"

while ($true) {
    $videos = Get-ChildItem -Path $watchFolder -Filter *.mp4 -ErrorAction SilentlyContinue
    
    foreach ($video in $videos) {
        Write-Log "发现新视频: $($video.Name)"
        
        # 移动到处理目录
        $processingPath = Join-Path $processingFolder $video.Name
        Move-Item -Path $video.FullName -Destination $processingPath -Force
        
        # 转码
        $outputName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name) + "_transcoded.mp4"
        $outputPath = Join-Path $completedFolder $outputName
        
        Write-Log "开始转码: $($video.Name)"
        $result = & "C:\VideoTranscode\scripts\transcode.ps1" -InputFile $processingPath -OutputFile $outputPath
        
        if ($result) {
            Write-Log "转码成功: $outputName"
            # 删除原文件
            Remove-Item -Path $processingPath -Force
        } else {
            Write-Log "转码失败: $($video.Name)"
        }
    }
    
    Start-Sleep -Seconds 10
}
'@

$watcherScript | Out-File -FilePath "$workDir\scripts\watcher.ps1" -Encoding UTF8
Write-Host "✓ 监控服务已创建" -ForegroundColor Green
Write-Host ""

# 6. 创建启动脚本
Write-Host "[6/6] 创建快捷启动脚本..." -ForegroundColor Yellow

$startScript = @'
# 启动转码监控服务
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File C:\VideoTranscode\scripts\watcher.ps1"
Write-Host "转码监控服务已启动" -ForegroundColor Green
'@

$startScript | Out-File -FilePath "$workDir\启动监控服务.ps1" -Encoding UTF8

# 创建桌面快捷方式
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "启动转码服务.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$workDir\启动监控服务.ps1`""
$shortcut.WorkingDirectory = $workDir
$shortcut.IconLocation = "shell32.dll,137"
$shortcut.Save()

Write-Host "✓ 启动脚本已创建" -ForegroundColor Green
Write-Host ""

# 完成
Write-Host "========================================" -ForegroundColor Green
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Cyan
Write-Host "1. 打开 Chrome 浏览器访问 speedtest.net 测速" -ForegroundColor White
Write-Host "2. 打开 Telegram Desktop 登录账号" -ForegroundColor White
Write-Host "3. 双击桌面的'启动转码服务'快捷方式启动监控" -ForegroundColor White
Write-Host "4. 将视频文件放入 C:\VideoTranscode\downloads 自动转码" -ForegroundColor White
Write-Host ""
Write-Host "工作目录: $workDir" -ForegroundColor Yellow
Write-Host "日志目录: $workDir\logs" -ForegroundColor Yellow
Write-Host ""

# 打开 Chrome 进行测速
Write-Host "正在打开 Chrome 浏览器..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "chrome.exe" "https://www.speedtest.net/"

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
'@