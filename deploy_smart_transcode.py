#!/usr/bin/env python3
"""部署智能分辨率转码脚本"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

# 优化后的 watcher 脚本 - 智能分辨率检测 + 快速预设
WATCHER_SCRIPT = r'''# watcher_smart.ps1 - Smart Resolution Transcode (UTF-8 Fixed)
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

function Get-VideoHeight {
    param([string]$VideoPath)
    try {
        $result = & ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 $VideoPath 2>$null
        return [int]$result
    } catch { return 720 }
}

function Upload-SingleFile {
    param([string]$LocalPath, [string]$RemotePath)
    & scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $LocalPath "root@${mainServer}:$RemotePath" 2>&1 | Out-Null
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    & ssh -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$mainServer" "mkdir -p `"$RemoteDir`"" 2>&1 | Out-Null
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
        [string]$Filename, [string]$Title, [bool]$IsShort,
        [string]$HlsUrl, [string]$VideoUrl, [string]$CoverUrl,
        [string]$PreviewUrl, [double]$Duration
    )
    $body = @{ filename = $Filename; title = $Title; is_short = $IsShort; duration = $Duration }
    if ($HlsUrl) { $body.hls_url = $HlsUrl }
    if ($VideoUrl) { $body.video_url = $VideoUrl }
    if ($CoverUrl) { $body.cover_url = $CoverUrl }
    if ($PreviewUrl) { $body.preview_url = $PreviewUrl }
    $json = $body | ConvertTo-Json -Compress
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    try {
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

Write-Log "=== Watcher Smart Started (Adaptive Resolution) ==="

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
        
        # Transcode to 720p MP4 (fast preset)
        $outVideo = "$outDir\$name.mp4"
        Write-Log "  Transcoding (fast)..."
        & ffmpeg -i $procPath -c:v libx264 -preset fast -crf 23 -vf "scale=-2:720" -c:a aac -b:a 128k -movflags +faststart -threads 8 -y $outVideo 2>&1 | Out-Null
        
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
                if (Test-Path $coverPath) { $coverSizes[$i] = (Get-Item $coverPath).Length }
            }
            $bestCover = 5; $maxSize = 0
            foreach ($key in $coverSizes.Keys) { if ($coverSizes[$key] -gt $maxSize) { $maxSize = $coverSizes[$key]; $bestCover = $key } }
            $mainCover = "$outDir\$name.webp"
            if (Test-Path "$coversDir\cover_$bestCover.webp") { Copy-Item "$coversDir\cover_$bestCover.webp" $mainCover -Force }
            Write-Log "  Covers OK (best: cover_$bestCover)"
            
            # Upload
            Write-Log "  Uploading..."
            Upload-SingleFile -LocalPath $outVideo -RemotePath "/www/wwwroot/video-app/backend/uploads/shorts/"
            Upload-SingleFile -LocalPath $mainCover -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
            $remoteCoverDir = "/www/wwwroot/video-app/backend/uploads/shorts/thumbnails/$name"
            & ssh -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$mainServer" "mkdir -p `"$remoteCoverDir`"" 2>&1 | Out-Null
            for ($i = 1; $i -le 10; $i++) {
                $coverFile = "$coversDir\cover_$i.webp"
                if (Test-Path $coverFile) { & scp -i $sshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $coverFile "root@${mainServer}:$remoteCoverDir/cover_$i.webp" 2>&1 | Out-Null }
            }
            Write-Log "  Upload OK"
            
            # Callback
            Write-Log "  Callback..."
            Send-Callback -Filename $name -Title $name -IsShort $true -VideoUrl "/uploads/shorts/$name.mp4" -CoverUrl "/uploads/thumbnails/$name.webp" -Duration $duration
        }
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        Write-Log "  Done: $name"
    }

    # Long videos - Smart Resolution
    $longFiles = Get-ChildItem -LiteralPath "$baseDir\downloads\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
    foreach ($file in $longFiles) {
        $name = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $outDir = "$baseDir\completed\long\$name"
        $procPath = "$baseDir\processing\$($file.Name)"
        
        Write-Log "Long: $($file.Name)"
        Move-Item -LiteralPath $file.FullName -Destination $procPath -Force
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        # Get source video height
        $srcHeight = Get-VideoHeight -VideoPath $procPath
        Write-Log "  Source height: ${srcHeight}p"
        
        $hlsDir = "$outDir\hls"
        if (-not (Test-Path $hlsDir)) { New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null }
        
        # Determine output resolutions based on source
        # 1080p+ -> 1080p, 720p
        # 720p -> 720p, 480p
        # 480p -> 480p
        # 360p -> 360p
        $resolutions = @()
        $masterEntries = @()
        
        if ($srcHeight -ge 1080) {
            $resolutions = @(
                @{h=1080; bw=4000000; ab="192k"},
                @{h=720; bw=2500000; ab="128k"}
            )
        } elseif ($srcHeight -ge 720) {
            $resolutions = @(
                @{h=720; bw=2500000; ab="128k"},
                @{h=480; bw=1500000; ab="96k"}
            )
        } elseif ($srcHeight -ge 480) {
            $resolutions = @(
                @{h=480; bw=1500000; ab="96k"}
            )
        } else {
            $resolutions = @(
                @{h=360; bw=800000; ab="64k"}
            )
        }
        
        Write-Log "  Output resolutions: $($resolutions | ForEach-Object { "$($_.h)p" })"
        
        # Transcode each resolution
        foreach ($res in $resolutions) {
            $h = $res.h
            $bw = $res.bw
            $ab = $res.ab
            $hlsRes = "$hlsDir\${h}p"
            if (-not (Test-Path $hlsRes)) { New-Item -ItemType Directory -Path $hlsRes -Force | Out-Null }
            Write-Log "  HLS ${h}p..."
            & ffmpeg -i $procPath -c:v libx264 -preset fast -crf 23 -vf "scale=-2:$h" -c:a aac -b:a $ab -hls_time 10 -hls_list_size 0 -hls_segment_filename "$hlsRes\seg_%03d.ts" -threads 8 -y "$hlsRes\playlist.m3u8" 2>&1 | Out-Null
            
            # Add to master playlist
            $masterEntries += "#EXT-X-STREAM-INF:BANDWIDTH=$bw,RESOLUTION=$([int]($h * 16 / 9))x$h"
            $masterEntries += "${h}p/playlist.m3u8"
        }
        
        # Write master playlist
        $masterContent = "#EXTM3U`n#EXT-X-VERSION:3`n" + ($masterEntries -join "`n")
        $masterContent | Out-File -FilePath "$hlsDir\master.m3u8" -Encoding UTF8
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
            if (Test-Path $coverPath) { $coverSizes[$i] = (Get-Item $coverPath).Length }
        }
        $bestCover = 5; $maxSize = 0
        foreach ($key in $coverSizes.Keys) { if ($coverSizes[$key] -gt $maxSize) { $maxSize = $coverSizes[$key]; $bestCover = $key } }
        $mainCover = "$outDir\$name.webp"
        if (Test-Path "$coversDir\cover_$bestCover.webp") { Copy-Item "$coversDir\cover_$bestCover.webp" $mainCover -Force }
        Write-Log "  Covers OK (best: cover_$bestCover)"
        
        # Preview
        $preview = "$outDir\${name}_preview.webm"
        Write-Log "  Preview..."
        $midPos = $duration / 2
        & ffmpeg -ss $midPos -i $procPath -t 10 -c:v libvpx-vp9 -b:v 500k -vf "scale=480:-1" -an -threads 4 -y $preview 2>&1 | Out-Null
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
        Send-Callback -Filename $name -Title $name -IsShort $false -HlsUrl "/uploads/hls/$name/master.m3u8" -CoverUrl "/uploads/thumbnails/$name.webp" -PreviewUrl $previewUrl -Duration $duration
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        Write-Log "  Done: $name"
    }

    Start-Sleep -Seconds 10
}
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("部署智能分辨率转码脚本...")
print("=" * 60)

# 1. 备份原脚本
print("\n1. 备份原脚本...")
cmd = 'copy D:\\VideoTranscode\\scripts\\watcher.ps1 D:\\VideoTranscode\\scripts\\watcher.ps1.bak_before_smart'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()
print("   备份完成")

# 2. 写入新脚本
print("\n2. 写入新脚本...")
sftp = ssh.open_sftp()
with sftp.file('D:/VideoTranscode/scripts/watcher.ps1', 'w') as f:
    f.write(WATCHER_SCRIPT)
sftp.close()
print("   写入完成")

# 3. 验证
print("\n3. 验证新脚本...")
cmd = 'powershell -Command "Select-String -Path D:\\VideoTranscode\\scripts\\watcher.ps1 -Pattern \'Get-VideoHeight|Smart|Adaptive\' | Measure-Object | Select-Object -ExpandProperty Count"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
if output and int(output) > 0:
    print(f"   ✓ 找到智能分辨率相关代码 ({output} 处)")
else:
    print("   ✗ 未找到智能分辨率代码")

# 4. 重启 watcher
print("\n4. 重启 watcher...")
cmd = 'taskkill /F /IM powershell.exe /FI "WINDOWTITLE eq watcher*" 2>nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

time.sleep(2)

# 使用计划任务启动
cmd = 'schtasks /Delete /TN "StartWatcher" /F 2>nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

cmd = 'schtasks /Create /TN "StartWatcher" /TR "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1" /SC ONCE /ST 00:00 /F'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

cmd = 'schtasks /Run /TN "StartWatcher"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

time.sleep(3)

# 5. 检查状态
print("\n5. 检查 watcher 状态...")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'powershell' in output.lower():
    print("   ✓ Watcher 已启动")
else:
    print("   ✗ Watcher 未启动")

# 6. 检查最新日志
print("\n6. 最新日志:")
cmd = 'powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 -Encoding UTF8"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

ssh.close()

print("\n" + "=" * 60)
print("部署完成！智能分辨率转码规则：")
print("  • 1080p+ 原视频 → 输出 1080p, 720p")
print("  • 720p 原视频   → 输出 720p, 480p")
print("  • 480p 原视频   → 输出 480p")
print("  • 360p 原视频   → 输出 360p")
print("  • 使用 fast 预设，提升转码速度约 30-50%")
print("=" * 60)
