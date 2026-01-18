#!/usr/bin/env python3
"""
部署转码脚本 v2 到转码服务器
- HLS 多码率 (长视频)
- MP4 720p (短视频)
- 智能多封面
- 预览视频 (仅长视频)
- 上传后设为未发布状态
"""
import paramiko
import os

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"
MAIN_SERVER = "38.47.218.137"

print("🚀 部署转码脚本 v2")
print("=" * 60)

# 读取本地脚本
with open("scripts/transcode_v2.ps1", "r", encoding="utf-8") as f:
    transcode_script = f.read()

# 创建新的 watcher 脚本
watcher_script = '''# watcher_v2.ps1 - 视频监控服务 v2
# 支持 HLS 多码率 + 智能封面
# 部署到: D:\\VideoTranscode\\scripts\\watcher.ps1

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$baseDir = "D:\\VideoTranscode"
$downloadsDir = "$baseDir\\downloads"
$processingDir = "$baseDir\\processing"
$completedDir = "$baseDir\\completed"
$logFile = "$baseDir\\logs\\watcher.log"

# 服务器配置
$mainServer = "38.47.218.137"
$sshKey = "C:\\server_key"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append -Encoding UTF8
}

function Get-VideoDuration {
    param([string]$VideoPath)
    try {
        $result = & ffprobe -v error -show_entries format=duration -of csv=p=0 $VideoPath 2>$null
        return [double]$result
    } catch {
        return 0
    }
}

function Upload-ToMainServer {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$VideoType
    )
    
    Write-Log "  Uploading to main server..."
    
    # SCP 上传
    $scpCmd = "scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$LocalPath`" root@${mainServer}:$RemotePath"
    
    try {
        cmd /c $scpCmd 2>&1
        Write-Log "  Upload completed"
        return $true
    } catch {
        Write-Log "  Upload failed: $_"
        return $false
    }
}

function Upload-Directory {
    param(
        [string]$LocalDir,
        [string]$RemoteDir
    )
    
    Write-Log "  Uploading directory..."
    
    # 递归上传目录
    $scpCmd = "scp -r -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$LocalDir`" root@${mainServer}:$RemoteDir"
    
    try {
        cmd /c $scpCmd 2>&1
        return $true
    } catch {
        return $false
    }
}

Write-Log "=== Watcher v2 Started ==="

while ($true) {
    # 扫描 short 和 long 目录
    $shortFiles = Get-ChildItem -Path "$downloadsDir\\short" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    $longFiles = Get-ChildItem -Path "$downloadsDir\\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    
    # 处理短视频
    foreach ($file in $shortFiles) {
        Write-Log "Found short video: $($file.Name)"
        
        $inputPath = $file.FullName
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outputDir = "$completedDir\\short\\$baseName"
        
        # 移动到处理目录
        $processingPath = "$processingDir\\$($file.Name)"
        Move-Item -LiteralPath $inputPath -Destination $processingPath -Force
        
        Write-Log "  Starting transcode (short)..."
        
        # 调用转码脚本
        $transcodeCmd = "powershell -ExecutionPolicy Bypass -File `"$baseDir\\scripts\\transcode_v2.ps1`" -InputFile `"$processingPath`" -OutputDir `"$outputDir`" -VideoType short"
        
        try {
            Invoke-Expression $transcodeCmd
            
            # 上传到主服务器
            if (Test-Path "$outputDir\\$baseName.mp4") {
                Upload-ToMainServer -LocalPath "$outputDir\\$baseName.mp4" -RemotePath "/www/wwwroot/video-app/backend/uploads/shorts/" -VideoType "short"
            }
            
            # 上传封面
            if (Test-Path "$outputDir\\covers") {
                Upload-Directory -LocalDir "$outputDir\\covers" -RemoteDir "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            }
            
            # 删除处理文件
            Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            
            Write-Log "  Completed: $baseName"
        } catch {
            Write-Log "  Error: $_"
        }
    }
    
    # 处理长视频
    foreach ($file in $longFiles) {
        Write-Log "Found long video: $($file.Name)"
        
        $inputPath = $file.FullName
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outputDir = "$completedDir\\long\\$baseName"
        
        # 移动到处理目录
        $processingPath = "$processingDir\\$($file.Name)"
        Move-Item -LiteralPath $inputPath -Destination $processingPath -Force
        
        Write-Log "  Starting transcode (long/HLS)..."
        
        # 调用转码脚本
        $transcodeCmd = "powershell -ExecutionPolicy Bypass -File `"$baseDir\\scripts\\transcode_v2.ps1`" -InputFile `"$processingPath`" -OutputDir `"$outputDir`" -VideoType long"
        
        try {
            Invoke-Expression $transcodeCmd
            
            # 上传 HLS 目录
            if (Test-Path "$outputDir\\hls") {
                Upload-Directory -LocalDir "$outputDir\\hls" -RemoteDir "/www/wwwroot/video-app/backend/uploads/hls/$baseName/"
            }
            
            # 上传封面
            if (Test-Path "$outputDir\\covers") {
                Upload-Directory -LocalDir "$outputDir\\covers" -RemoteDir "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            }
            
            # 上传预览
            if (Test-Path "$outputDir\\${baseName}_preview.webm") {
                Upload-ToMainServer -LocalPath "$outputDir\\${baseName}_preview.webm" -RemotePath "/www/wwwroot/video-app/backend/uploads/previews/" -VideoType "long"
            }
            
            # 删除处理文件
            Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            
            Write-Log "  Completed: $baseName"
        } catch {
            Write-Log "  Error: $_"
        }
    }
    
    Start-Sleep -Seconds 10
}
'''

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 {TRANSCODE_SERVER}...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!")
    
    # 停止现有 watcher
    print("\n🛑 停止现有 watcher...")
    ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
    
    # 创建必要目录
    print("\n📁 创建目录结构...")
    dirs = [
        "D:\\VideoTranscode\\completed\\short",
        "D:\\VideoTranscode\\completed\\long",
        "D:\\VideoTranscode\\downloads\\short",
        "D:\\VideoTranscode\\downloads\\long",
        "D:\\VideoTranscode\\processing",
        "D:\\VideoTranscode\\logs",
        "D:\\VideoTranscode\\scripts"
    ]
    for d in dirs:
        ssh.exec_command(f'if not exist "{d}" mkdir "{d}"', timeout=30)
    
    # 上传转码脚本
    print("\n📤 上传 transcode_v2.ps1...")
    sftp = ssh.open_sftp()
    with sftp.file("D:/VideoTranscode/scripts/transcode_v2.ps1", "w") as f:
        f.write(transcode_script)
    
    # 上传 watcher 脚本
    print("📤 上传 watcher.ps1...")
    with sftp.file("D:/VideoTranscode/scripts/watcher.ps1", "w") as f:
        f.write(watcher_script)
    
    sftp.close()
    
    # 启动 watcher
    print("\n🚀 启动 watcher...")
    ssh.exec_command('start /B powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)
    
    import time
    time.sleep(3)
    
    # 验证
    print("\n✅ 验证部署...")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore')
    
    if 'powershell.exe' in output:
        print("✅ Watcher 正在运行!")
    else:
        print("⚠️ Watcher 可能未启动，请手动检查")
    
    print("\n" + "=" * 60)
    print("🎉 部署完成!")
    print("=" * 60)
    print("\n📋 新功能:")
    print("  - 短视频: MP4 (720p) + 多封面")
    print("  - 长视频: HLS 多码率 (720p/480p/360p) + 多封面 + 预览")
    print("  - 智能封面评分排序")
    print("\n📁 目录结构:")
    print("  - downloads/short/ - 放入短视频")
    print("  - downloads/long/  - 放入长视频")
    print("  - completed/short/ - 短视频输出")
    print("  - completed/long/  - 长视频输出 (含 HLS)")
    
except Exception as e:
    print(f"\n❌ 部署失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'ssh' in locals():
        ssh.close()
