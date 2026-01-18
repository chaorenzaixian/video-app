#!/usr/bin/env python3
"""部署 watcher v2"""
import paramiko
import time

WATCHER_SCRIPT = r'''# watcher_v2.ps1 - Video Watcher Service v2
# HLS multi-bitrate + smart covers
# Deploy to: D:\VideoTranscode\scripts\watcher.ps1

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$baseDir = "D:\VideoTranscode"
$downloadsDir = "$baseDir\downloads"
$processingDir = "$baseDir\processing"
$completedDir = "$baseDir\completed"
$logFile = "$baseDir\logs\watcher.log"

$mainServer = "38.47.218.137"
$sshKey = "C:\server_key"

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

function Upload-File {
    param([string]$LocalPath, [string]$RemotePath)
    
    $scpCmd = "scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$LocalPath`" root@${mainServer}:$RemotePath"
    try {
        cmd /c $scpCmd 2>&1 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    
    $scpCmd = "scp -r -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$LocalDir`" root@${mainServer}:$RemoteDir"
    try {
        cmd /c $scpCmd 2>&1 | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Log "=== Watcher v2 Started - HLS + Smart Covers ==="

while ($true) {
    # Scan short videos
    $shortFiles = Get-ChildItem -LiteralPath "$downloadsDir\short" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    
    foreach ($file in $shortFiles) {
        Write-Log "Found short video: $($file.Name)"
        
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outputDir = "$completedDir\short\$baseName"
        $processingPath = "$processingDir\$($file.Name)"
        
        # Move to processing
        Move-Item -LiteralPath $file.FullName -Destination $processingPath -Force
        Write-Log "  Moved to processing"
        
        # Create output dir
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        Write-Log "  Starting transcode (short/MP4)..."
        
        # Call transcode script
        try {
            & powershell -ExecutionPolicy Bypass -File "$baseDir\scripts\transcode_v2.ps1" -InputFile $processingPath -OutputDir $outputDir -VideoType short
            
            # Upload video
            $videoFile = "$outputDir\$baseName.mp4"
            if (Test-Path $videoFile) {
                Write-Log "  Uploading video..."
                Upload-File -LocalPath $videoFile -RemotePath "/www/wwwroot/video-app/backend/uploads/shorts/"
            }
            
            # Upload main cover
            $coverFile = "$outputDir\$baseName.webp"
            if (Test-Path $coverFile) {
                Write-Log "  Uploading cover..."
                Upload-File -LocalPath $coverFile -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            }
            
            # Upload all covers
            $coversDir = "$outputDir\covers"
            if (Test-Path $coversDir) {
                Write-Log "  Uploading cover candidates..."
                Upload-Directory -LocalDir $coversDir -RemoteDir "/www/wwwroot/video-app/backend/uploads/thumbnails/$baseName/"
            }
            
            # Cleanup
            Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            
            Write-Log "  Completed: $baseName"
        } catch {
            Write-Log "  Error: $_"
        }
    }
    
    # Scan long videos
    $longFiles = Get-ChildItem -LiteralPath "$downloadsDir\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    
    foreach ($file in $longFiles) {
        Write-Log "Found long video: $($file.Name)"
        
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outputDir = "$completedDir\long\$baseName"
        $processingPath = "$processingDir\$($file.Name)"
        
        # Move to processing
        Move-Item -LiteralPath $file.FullName -Destination $processingPath -Force
        Write-Log "  Moved to processing"
        
        # Create output dir
        if (-not (Test-Path $outputDir)) {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        
        Write-Log "  Starting transcode (long/HLS)..."
        
        try {
            & powershell -ExecutionPolicy Bypass -File "$baseDir\scripts\transcode_v2.ps1" -InputFile $processingPath -OutputDir $outputDir -VideoType long
            
            # Upload HLS directory
            $hlsDir = "$outputDir\hls"
            if (Test-Path $hlsDir) {
                Write-Log "  Uploading HLS..."
                # Create remote dir first
                $sshCmd = "ssh -i $sshKey -o StrictHostKeyChecking=no root@$mainServer `"mkdir -p /www/wwwroot/video-app/backend/uploads/hls/$baseName`""
                cmd /c $sshCmd 2>&1 | Out-Null
                Upload-Directory -LocalDir $hlsDir -RemoteDir "/www/wwwroot/video-app/backend/uploads/hls/$baseName/"
            }
            
            # Upload main cover
            $coverFile = "$outputDir\$baseName.webp"
            if (Test-Path $coverFile) {
                Write-Log "  Uploading cover..."
                Upload-File -LocalPath $coverFile -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            }
            
            # Upload cover candidates
            $coversDir = "$outputDir\covers"
            if (Test-Path $coversDir) {
                Write-Log "  Uploading cover candidates..."
                Upload-Directory -LocalDir $coversDir -RemoteDir "/www/wwwroot/video-app/backend/uploads/thumbnails/$baseName/"
            }
            
            # Upload preview
            $previewFile = "$outputDir\${baseName}_preview.webm"
            if (Test-Path $previewFile) {
                Write-Log "  Uploading preview..."
                Upload-File -LocalPath $previewFile -RemotePath "/www/wwwroot/video-app/backend/uploads/previews/"
            }
            
            # Cleanup
            Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
            
            Write-Log "  Completed: $baseName"
        } catch {
            Write-Log "  Error: $_"
        }
    }
    
    Start-Sleep -Seconds 10
}
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print("🚀 部署 Watcher v2")
print("=" * 60)

# 停止现有 watcher
print("🛑 停止现有 watcher...")
ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
time.sleep(2)

# 上传新脚本
print("📤 上传 watcher.ps1...")
sftp = ssh.open_sftp()
with sftp.file("/D:/VideoTranscode/scripts/watcher.ps1", "w") as f:
    f.write(WATCHER_SCRIPT)
sftp.close()

# 验证
stdin, stdout, stderr = ssh.exec_command('powershell -Command "(Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 -Head 3) -join \' | \'"', timeout=30)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"  验证: {content[:80]}...")

# 启动 watcher
print("\n🚀 启动 watcher...")
ssh.exec_command('schtasks /Run /TN "VideoWatcherService"', timeout=30)
time.sleep(3)

# 检查状态
stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
output = stdout.read().decode('gbk', errors='ignore')
if 'powershell.exe' in output:
    print("✅ Watcher v2 正在运行!")
else:
    print("⚠️ 直接启动...")
    ssh.exec_command('start "" powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)

# 等待日志
time.sleep(5)
print("\n📝 最新日志:")
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 -ErrorAction SilentlyContinue"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
print(log if log else "(无日志)")

ssh.close()
print("\n✅ 部署完成!")
print("\n📋 新功能:")
print("  - 短视频: MP4 (720p) + 多封面")
print("  - 长视频: HLS 多码率 + 多封面 + 预览")
print("  - 智能封面评分排序")
print("\n📁 使用方法:")
print("  - 短视频放入: downloads/short/")
print("  - 长视频放入: downloads/long/")
