#!/usr/bin/env python3
"""部署修复编码问题的watcher脚本"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

# 完整的修复后的watcher脚本
WATCHER_SCRIPT = r'''# watcher_final.ps1 - Video Watcher Final Version (UTF-8 Fixed)
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

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
    & scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $LocalPath "root@${mainServer}:$RemotePath" 2>&1 | Out-Null
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    # Create remote directory
    & ssh -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$mainServer" "mkdir -p `"$RemoteDir`"" 2>&1 | Out-Null
    
    # Upload each file
    $files = Get-ChildItem -LiteralPath $LocalDir -File -Recurse
    foreach ($f in $files) {
        $relativePath = $f.FullName.Substring($LocalDir.Length + 1).Replace('\', '/')
        $remoteFile = "$RemoteDir/$relativePath"
        $remoteFileDir = Split-Path $remoteFile -Parent
        
        & ssh -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$mainServer" "mkdir -p `"$remoteFileDir`"" 2>&1 | Out-Null
        & scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $f.FullName "root@${mainServer}:$remoteFile" 2>&1 | Out-Null
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

    # 使用 UTF-8 编码 JSON
    $json = $body | ConvertTo-Json -Compress
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    
    try {
        # 使用 WebRequest 以确保 UTF-8 编码
        $request = [System.Net.HttpWebRequest]::Create("$apiBase/admin/videos/import-from-transcode")
        $request.Method = "POST"
        $request.ContentType = "application/json; charset=utf-8"
        $request.Headers.Add("X-Transcode-Key", $transcodeKey)
        $request.ContentLength = $utf8Bytes.Length
        $request.Timeout = 30000
        
        $stream = $request.GetRequestStream()
        $stream.Write($utf8Bytes, 0, $utf8Bytes.Length)
        $stream.Close()
        
        $response = $request.GetResponse()
        $reader = New-Object System.IO.StreamReader($response.GetResponseStream(), [System.Text.Encoding]::UTF8)
        $result = $reader.ReadToEnd()
        $reader.Close()
        $response.Close()
        
        Write-Log "    Callback OK: $result"
        return $true
    } catch {
        Write-Log "    Callback FAILED: $_"
        return $false
    }
}

Write-Log "=== Watcher Final Started (UTF-8 Fixed) ==="

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
            
            # Generate covers
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

            # Select best cover
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
            
            # Upload main cover
            Upload-SingleFile -LocalPath $mainCover -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            
            # Upload all candidate covers to shorts/thumbnails/{name}/
            $remoteCoverDir = "/www/wwwroot/video-app/backend/uploads/shorts/thumbnails/$name"
            & ssh -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$mainServer" "mkdir -p `"$remoteCoverDir`"" 2>&1 | Out-Null
            for ($i = 1; $i -le 10; $i++) {
                $coverFile = "$coversDir\cover_$i.webp"
                if (Test-Path $coverFile) {
                    & scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $coverFile "root@${mainServer}:$remoteCoverDir/cover_$i.webp" 2>&1 | Out-Null
                }
            }
            Write-Log "  Upload OK"
            
            # Callback
            Write-Log "  Callback..."
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
        
        # Covers
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
        
        # Preview
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
        Write-Log "  Callback..."
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
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 1. 备份原脚本
print("1. 备份原脚本...")
cmd = 'copy D:\\VideoTranscode\\scripts\\watcher.ps1 D:\\VideoTranscode\\scripts\\watcher.ps1.bak_encoding'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

# 2. 写入新脚本（使用UTF-8 BOM）
print("2. 写入新脚本...")

# 将脚本写入临时文件
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8-sig', suffix='.ps1', delete=False) as f:
    f.write(WATCHER_SCRIPT)
    temp_file = f.name

# 使用SFTP上传
sftp = ssh.open_sftp()
sftp.put(temp_file, 'D:/VideoTranscode/scripts/watcher.ps1')
sftp.close()

os.unlink(temp_file)

# 3. 验证
print("3. 验证新脚本...")
cmd = 'type D:\\VideoTranscode\\scripts\\watcher.ps1 | findstr "UTF-8 charset WebRequest"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"验证结果:\n{output}")

# 4. 重启watcher服务
print("4. 重启watcher服务...")
# 先停止现有的watcher进程
cmd = 'taskkill /F /IM powershell.exe /FI "WINDOWTITLE eq watcher*" 2>nul & echo OK'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

# 启动新的watcher
cmd = 'start "watcher" powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

print("5. 检查watcher是否运行...")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

ssh.close()
print("\n完成! 新的watcher脚本已部署，支持UTF-8中文编码。")
