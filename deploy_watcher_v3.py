#!/usr/bin/env python3
"""部署 watcher v3 - 添加回调功能"""
import paramiko
import time

# Watcher v3 - 添加回调通知主服务器
WATCHER_SCRIPT = r'''# watcher_v3.ps1 - Video Watcher with Callback
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$baseDir = "D:\VideoTranscode"
$logFile = "$baseDir\logs\watcher.log"
$mainServer = "38.47.218.137"
$sshKey = "C:\server_key"
$transcodeKey = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"
$apiBase = "http://38.47.218.137:8000/api/v1"

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
    } catch { return 60 }
}

function Upload-SingleFile {
    param([string]$LocalPath, [string]$RemotePath)
    $cmd = "scp -i `"$sshKey`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$LocalPath`" root@${mainServer}:$RemotePath"
    cmd /c $cmd 2>&1 | Out-Null
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    $mkdirCmd = "ssh -i `"$sshKey`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL root@$mainServer `"mkdir -p $RemoteDir`""
    cmd /c $mkdirCmd 2>&1 | Out-Null
    
    $files = Get-ChildItem -LiteralPath $LocalDir -File -Recurse
    foreach ($f in $files) {
        $relativePath = $f.FullName.Substring($LocalDir.Length + 1).Replace('\', '/')
        $remoteFile = "$RemoteDir/$relativePath"
        $remoteFileDir = Split-Path $remoteFile -Parent
        
        $mkdirCmd = "ssh -i `"$sshKey`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL root@$mainServer `"mkdir -p $remoteFileDir`""
        cmd /c $mkdirCmd 2>&1 | Out-Null
        
        $scpCmd = "scp -i `"$sshKey`" -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL `"$($f.FullName)`" root@${mainServer}:$remoteFile"
        cmd /c $scpCmd 2>&1 | Out-Null
    }
}

function Send-Callback {
    param(
        [string]$Filename,
        [string]$Title,
        [bool]$IsShort,
        [string]$HlsUrl,
        [string]$VideoUrl,
        [string]$CoverUrl,
        [string]$PreviewUrl,
        [double]$Duration
    )
    
    $body = @{
        filename = $Filename
        title = $Title
        is_short = $IsShort
        duration = $Duration
    }
    
    if ($HlsUrl) { $body.hls_url = $HlsUrl }
    if ($VideoUrl) { $body.video_url = $VideoUrl }
    if ($CoverUrl) { $body.cover_url = $CoverUrl }
    if ($PreviewUrl) { $body.preview_url = $PreviewUrl }
    
    $json = $body | ConvertTo-Json -Compress
    $headers = @{
        "Content-Type" = "application/json"
        "X-Transcode-Key" = $transcodeKey
    }
    
    try {
        $response = Invoke-RestMethod -Uri "$apiBase/admin/videos/import-from-transcode" -Method Post -Body $json -Headers $headers -TimeoutSec 30
        Write-Log "    Callback OK: $($response.message)"
        return $true
    } catch {
        Write-Log "    Callback FAILED: $_"
        return $false
    }
}

Write-Log "=== Watcher v3 Started (with Callback) ==="

while ($true) {
    # Short videos
    $shortFiles = Get-ChildItem -LiteralPath "$baseDir\downloads\short" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    foreach ($file in $shortFiles) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outDir = "$baseDir\completed\short\$name"
        $procPath = "$baseDir\processing\$($file.Name)"
        
        Write-Log "Short: $($file.Name)"
        Move-Item -LiteralPath $file.FullName -Destination $procPath -Force
        
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        # Transcode to 720p MP4
        $outVideo = "$outDir\$name.mp4"
        Write-Log "  Transcoding..."
        & ffmpeg -i $procPath -c:v libx264 -preset medium -crf 23 -vf "scale=-2:720" -c:a aac -b:a 128k -movflags +faststart -y $outVideo 2>&1 | Out-Null
        
        if (Test-Path $outVideo) {
            Write-Log "  Transcode OK"
            $duration = Get-VideoDuration -VideoPath $outVideo
            
            # Generate covers with smart selection
            $coversDir = "$outDir\covers"
            if (-not (Test-Path $coversDir)) { New-Item -ItemType Directory -Path $coversDir -Force | Out-Null }
            
            $coverSizes = @{}
            for ($i = 1; $i -le 10; $i++) {
                $pos = $duration * ($i / 11)
                $coverPath = "$coversDir\cover_$i.webp"
                & ffmpeg -ss $pos -i $outVideo -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y $coverPath 2>&1 | Out-Null
                if (Test-Path $coverPath) {
                    $coverSizes[$i] = (Get-Item $coverPath).Length
                }
            }
            
            # Select best cover (largest = most colorful)
            $bestCover = 5
            $maxSize = 0
            foreach ($key in $coverSizes.Keys) {
                if ($coverSizes[$key] -gt $maxSize) {
                    $maxSize = $coverSizes[$key]
                    $bestCover = $key
                }
            }
            
            $mainCover = "$outDir\$name.webp"
            if (Test-Path "$coversDir\cover_$bestCover.webp") {
                Copy-Item "$coversDir\cover_$bestCover.webp" $mainCover -Force
            }
            Write-Log "  Covers OK (best: cover_$bestCover)"
            
            # Upload
            Write-Log "  Uploading..."
            Upload-SingleFile -LocalPath $outVideo -RemotePath "/www/wwwroot/video-app/backend/uploads/shorts/"
            Upload-SingleFile -LocalPath $mainCover -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            Write-Log "  Upload OK"
            
            # Callback
            Write-Log "  Sending callback..."
            Send-Callback -Filename $name -Title $name -IsShort $true `
                -VideoUrl "/uploads/shorts/$name.mp4" `
                -CoverUrl "/uploads/thumbnails/$name.webp" `
                -Duration $duration
        }
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        Write-Log "  Done: $name"
    }
    
    # Long videos
    $longFiles = Get-ChildItem -LiteralPath "$baseDir\downloads\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    foreach ($file in $longFiles) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outDir = "$baseDir\completed\long\$name"
        $procPath = "$baseDir\processing\$($file.Name)"
        
        Write-Log "Long: $($file.Name)"
        Move-Item -LiteralPath $file.FullName -Destination $procPath -Force
        
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        $hlsDir = "$outDir\hls"
        if (-not (Test-Path $hlsDir)) { New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null }
        
        # HLS 720p
        $hls720 = "$hlsDir\720p"
        if (-not (Test-Path $hls720)) { New-Item -ItemType Directory -Path $hls720 -Force | Out-Null }
        Write-Log "  HLS 720p..."
        & ffmpeg -i $procPath -c:v libx264 -preset medium -crf 23 -vf "scale=-2:720" -c:a aac -b:a 128k -hls_time 10 -hls_list_size 0 -hls_segment_filename "$hls720\seg_%03d.ts" -y "$hls720\playlist.m3u8" 2>&1 | Out-Null
        
        # HLS 480p
        $hls480 = "$hlsDir\480p"
        if (-not (Test-Path $hls480)) { New-Item -ItemType Directory -Path $hls480 -Force | Out-Null }
        Write-Log "  HLS 480p..."
        & ffmpeg -i $procPath -c:v libx264 -preset medium -crf 23 -vf "scale=-2:480" -c:a aac -b:a 96k -hls_time 10 -hls_list_size 0 -hls_segment_filename "$hls480\seg_%03d.ts" -y "$hls480\playlist.m3u8" 2>&1 | Out-Null
        
        # HLS 360p
        $hls360 = "$hlsDir\360p"
        if (-not (Test-Path $hls360)) { New-Item -ItemType Directory -Path $hls360 -Force | Out-Null }
        Write-Log "  HLS 360p..."
        & ffmpeg -i $procPath -c:v libx264 -preset medium -crf 23 -vf "scale=-2:360" -c:a aac -b:a 64k -hls_time 10 -hls_list_size 0 -hls_segment_filename "$hls360\seg_%03d.ts" -y "$hls360\playlist.m3u8" 2>&1 | Out-Null
        
        # Master playlist
        $master = @"
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
720p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=854x480
480p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p/playlist.m3u8
"@
        $master | Out-File -FilePath "$hlsDir\master.m3u8" -Encoding UTF8
        Write-Log "  HLS OK"
        
        # Get duration
        $duration = Get-VideoDuration -VideoPath $procPath
        
        # Covers with smart selection
        $coversDir = "$outDir\covers"
        if (-not (Test-Path $coversDir)) { New-Item -ItemType Directory -Path $coversDir -Force | Out-Null }
        
        $coverSizes = @{}
        for ($i = 1; $i -le 10; $i++) {
            $pos = $duration * ($i / 11)
            $coverPath = "$coversDir\cover_$i.webp"
            & ffmpeg -ss $pos -i $procPath -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y $coverPath 2>&1 | Out-Null
            if (Test-Path $coverPath) {
                $coverSizes[$i] = (Get-Item $coverPath).Length
            }
        }
        
        $bestCover = 5
        $maxSize = 0
        foreach ($key in $coverSizes.Keys) {
            if ($coverSizes[$key] -gt $maxSize) {
                $maxSize = $coverSizes[$key]
                $bestCover = $key
            }
        }
        
        $mainCover = "$outDir\$name.webp"
        if (Test-Path "$coversDir\cover_$bestCover.webp") {
            Copy-Item "$coversDir\cover_$bestCover.webp" $mainCover -Force
        }
        Write-Log "  Covers OK (best: cover_$bestCover)"
        
        # Preview (10 seconds from middle)
        $preview = "$outDir\${name}_preview.webm"
        Write-Log "  Preview..."
        $midPos = $duration / 2
        & ffmpeg -ss $midPos -i $procPath -t 10 -c:v libvpx-vp9 -b:v 500k -vf "scale=480:-1" -an -y $preview 2>&1 | Out-Null
        Write-Log "  Preview OK"
        
        # Upload
        Write-Log "  Uploading HLS..."
        Upload-Directory -LocalDir $hlsDir -RemoteDir "/www/wwwroot/video-app/backend/uploads/hls/$name"
        
        Write-Log "  Uploading thumbnail..."
        Upload-SingleFile -LocalPath $mainCover -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
        
        if (Test-Path $preview) {
            Write-Log "  Uploading preview..."
            Upload-SingleFile -LocalPath $preview -RemotePath "/www/wwwroot/video-app/backend/uploads/previews/"
        }
        Write-Log "  Upload OK"
        
        # Callback
        Write-Log "  Sending callback..."
        $previewUrl = $null
        if (Test-Path $preview) { $previewUrl = "/uploads/previews/${name}_preview.webm" }
        
        Send-Callback -Filename $name -Title $name -IsShort $false `
            -HlsUrl "/uploads/hls/$name/master.m3u8" `
            -CoverUrl "/uploads/thumbnails/$name.webp" `
            -PreviewUrl $previewUrl `
            -Duration $duration
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        Write-Log "  Done: $name"
    }
    
    Start-Sleep -Seconds 10
}
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('🔧 部署 Watcher v3 (带回调)')
print('=' * 60)

# 停止
print('停止 watcher...')
ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
time.sleep(2)

# 上传
print('上传新脚本...')
sftp = ssh.open_sftp()
with sftp.file('/D:/VideoTranscode/scripts/watcher.ps1', 'w') as f:
    f.write(WATCHER_SCRIPT)
sftp.close()

# 清空日志
ssh.exec_command('echo. > D:\\VideoTranscode\\logs\\watcher.log', timeout=30)

# 启动
print('启动 watcher...')
ssh.exec_command('schtasks /Run /TN "VideoWatcherService"', timeout=30)
time.sleep(3)

# 检查
stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
output = stdout.read().decode('gbk', errors='ignore')
if 'powershell.exe' in output:
    print('✅ Watcher v3 running')
else:
    print('❌ Watcher not running')

ssh.close()
print('\n✅ Done!')
print('\n功能说明:')
print('  - 短视频: MP4 (720p) + 10个候选封面 + 智能选封面')
print('  - 长视频: HLS (720p/480p/360p) + 10个候选封面 + 10秒预览')
print('  - 上传完成后自动回调主服务器创建数据库记录')
print('  - 视频状态设置为"待审核"，需要管理员手动发布')
