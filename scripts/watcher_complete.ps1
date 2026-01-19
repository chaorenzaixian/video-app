# watcher_complete.ps1 - 完整视频处理监控服务
# 功能: 监控下载目录，自动完成 转码→生成封面→生成HLS→上传→回调
# 支持: 长视频(HLS多分辨率) 和 短视频(单文件)
# 部署: D:\VideoTranscode\scripts\watcher.ps1

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# ========== Lock File for Guardian ==========
$lockFile = "D:\VideoTranscode\watcher.lock"
$PID | Out-File -FilePath $lockFile -Force -Encoding ASCII

# Clean up lock file on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Remove-Item "D:\VideoTranscode\watcher.lock" -Force -ErrorAction SilentlyContinue
}

# ========== 配置 ==========
$config = @{
    BaseDir = "D:\VideoTranscode"
    MainServer = "38.47.218.137"
    SshKey = "C:\server_key"
    TranscodeKey = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"
    ApiBase = "http://38.47.218.137:8000/api/v1"
    CheckInterval = 10
}

$logFile = "$($config.BaseDir)\logs\watcher_$(Get-Date -Format 'yyyyMMdd').log"

# 确保目录存在
@("downloads\long", "downloads\short", "processing", "completed\long", "completed\short", "logs") | ForEach-Object {
    $dir = Join-Path $config.BaseDir $_
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

# ========== 工具函数 ==========
function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append -Encoding UTF8
    Write-Host $logMessage -ForegroundColor $Color
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

# ========== 上传函数 ==========
function Upload-SingleFile {
    param([string]$LocalPath, [string]$RemotePath)
    
    if (-not (Test-Path -LiteralPath $LocalPath)) {
        Write-Log "  上传跳过: 文件不存在 $LocalPath" "Yellow"
        return $false
    }
    
    $fileName = [System.IO.Path]::GetFileName($LocalPath)
    $fileSize = [math]::Round((Get-Item -LiteralPath $LocalPath).Length / 1MB, 2)
    
    Write-Log "  上传: $fileName (${fileSize}MB)" "Gray"
    
    & scp -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $LocalPath "root@$($config.MainServer):$RemotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "  成功: $fileName" "Green"
        return $true
    } else {
        Write-Log "  失败: $fileName" "Red"
        return $false
    }
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    
    if (-not (Test-Path -LiteralPath $LocalDir)) {
        Write-Log "  上传跳过: 目录不存在 $LocalDir" "Yellow"
        return $false
    }
    
    # 创建远程目录
    & ssh -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$($config.MainServer)" "mkdir -p `"$RemoteDir`"" 2>&1 | Out-Null
    
    # 上传所有文件
    $files = Get-ChildItem -LiteralPath $LocalDir -File -Recurse
    $uploadCount = 0
    
    foreach ($f in $files) {
        $relativePath = $f.FullName.Substring($LocalDir.Length + 1).Replace('\', '/')
        $remoteFile = "$RemoteDir/$relativePath"
        $remoteFileDir = [System.IO.Path]::GetDirectoryName($remoteFile).Replace('\', '/')
        
        # 创建远程子目录
        & ssh -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$($config.MainServer)" "mkdir -p `"$remoteFileDir`"" 2>&1 | Out-Null
        
        # 上传文件
        & scp -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $f.FullName "root@$($config.MainServer):$remoteFile" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) { $uploadCount++ }
    }
    
    Write-Log "  目录上传完成: $uploadCount/$($files.Count) 文件" "Green"
    return $uploadCount -gt 0
}

# ========== 封面生成 ==========
function New-VideoCovers {
    param([string]$VideoPath, [string]$OutputDir, [double]$Duration, [int]$Count = 10)
    
    $coversDir = Join-Path $OutputDir "covers"
    if (-not (Test-Path $coversDir)) { New-Item -ItemType Directory -Path $coversDir -Force | Out-Null }
    
    Write-Log "  生成 $Count 张封面..." "Yellow"
    
    for ($i = 1; $i -le $Count; $i++) {
        $position = $Duration * ($i / ($Count + 1))
        $coverPath = Join-Path $coversDir "cover_$i.webp"
        
        & ffmpeg -ss $position -i $VideoPath -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y $coverPath 2>&1 | Out-Null
    }
    
    $generatedCount = (Get-ChildItem -Path $coversDir -Filter "cover_*.webp" -ErrorAction SilentlyContinue).Count
    Write-Log "  封面生成完成: $generatedCount 张" "Green"
    
    return $coversDir
}

function Get-BestCover {
    param([string]$CoversDir)
    
    $bestCover = 5
    $maxSize = 0
    
    for ($i = 1; $i -le 10; $i++) {
        $coverPath = Join-Path $CoversDir "cover_$i.webp"
        if (Test-Path $coverPath) {
            $size = (Get-Item $coverPath).Length
            # 优先选择中间位置(4-7)的大文件
            $positionBonus = if ($i -ge 4 -and $i -le 7) { 1.2 } else { 1.0 }
            $score = $size * $positionBonus
            if ($score -gt $maxSize) {
                $maxSize = $score
                $bestCover = $i
            }
        }
    }
    
    return $bestCover
}

# ========== HLS生成 ==========
function New-HlsStream {
    param([string]$VideoPath, [string]$OutputDir, [int]$SourceHeight)
    
    $hlsDir = Join-Path $OutputDir "hls"
    if (-not (Test-Path $hlsDir)) { New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null }
    
    Write-Log "  生成HLS流 (源高度: ${SourceHeight}p)..." "Yellow"
    
    # 根据源视频高度决定输出分辨率
    $resolutions = @()
    if ($SourceHeight -ge 1080) { $resolutions += @{name="1080p"; height=1080; bitrate="4000k"} }
    if ($SourceHeight -ge 720) { $resolutions += @{name="720p"; height=720; bitrate="2500k"} }
    if ($SourceHeight -ge 480) { $resolutions += @{name="480p"; height=480; bitrate="1200k"} }
    $resolutions += @{name="360p"; height=360; bitrate="800k"}
    
    # 生成各分辨率
    foreach ($res in $resolutions) {
        $resDir = Join-Path $hlsDir $res.name
        if (-not (Test-Path $resDir)) { New-Item -ItemType Directory -Path $resDir -Force | Out-Null }
        
        $playlistPath = Join-Path $resDir "playlist.m3u8"
        $segmentPattern = Join-Path $resDir "seg_%03d.ts"
        
        Write-Log "    生成 $($res.name)..." "Gray"
        
        & ffmpeg -i $VideoPath -c:v libx264 -preset fast -crf 23 `
            -vf "scale=-2:$($res.height)" `
            -c:a aac -b:a 128k `
            -f hls -hls_time 10 -hls_list_size 0 `
            -hls_segment_filename $segmentPattern `
            -y $playlistPath 2>&1 | Out-Null
    }
    
    # 生成master.m3u8
    $masterPath = Join-Path $hlsDir "master.m3u8"
    $masterContent = "#EXTM3U`n#EXT-X-VERSION:3`n"
    
    foreach ($res in $resolutions) {
        $bandwidth = [int]($res.bitrate.Replace("k", "")) * 1000
        $width = [int]($res.height * 16 / 9)
        $masterContent += "#EXT-X-STREAM-INF:BANDWIDTH=$bandwidth,RESOLUTION=${width}x$($res.height)`n"
        $masterContent += "$($res.name)/playlist.m3u8`n"
    }
    
    $masterContent | Out-File -FilePath $masterPath -Encoding UTF8 -NoNewline
    
    Write-Log "  HLS生成完成: $($resolutions.Count) 个分辨率" "Green"
    
    return $hlsDir
}

# ========== API回调 ==========
function Send-Callback {
    param(
        [string]$Filename,
        [string]$Title,
        [bool]$IsShort,
        [string]$HlsUrl = "",
        [string]$VideoUrl = "",
        [string]$CoverUrl = "",
        [string]$PreviewUrl = "",
        [double]$Duration = 0
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
    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    
    try {
        $request = [System.Net.HttpWebRequest]::Create("$($config.ApiBase)/admin/videos/import-from-transcode")
        $request.Method = "POST"
        $request.ContentType = "application/json; charset=utf-8"
        $request.Headers.Add("X-Transcode-Key", $config.TranscodeKey)
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
        
        Write-Log "  回调成功: $result" "Green"
        return $true
    } catch {
        Write-Log "  回调失败: $_" "Red"
        return $false
    }
}

# ========== 处理长视频 ==========
function Process-LongVideo {
    param([System.IO.FileInfo]$VideoFile)
    
    $name = [System.IO.Path]::GetFileNameWithoutExtension($VideoFile.Name)
    $outDir = Join-Path $config.BaseDir "completed\long\$name"
    $procPath = Join-Path $config.BaseDir "processing\$($VideoFile.Name)"
    
    Write-Log "==========================================" "Cyan"
    Write-Log "处理长视频: $($VideoFile.Name)" "Cyan"
    Write-Log "==========================================" "Cyan"
    
    try {
        # 移动到处理目录
        Move-Item -LiteralPath $VideoFile.FullName -Destination $procPath -Force
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        # 获取视频信息
        $duration = Get-VideoDuration -VideoPath $procPath
        $height = Get-VideoHeight -VideoPath $procPath
        Write-Log "  视频信息: 时长=${duration}秒, 高度=${height}p" "White"
        
        # 1. 生成HLS
        Write-Log "[1/4] 生成HLS流..." "Yellow"
        $hlsDir = New-HlsStream -VideoPath $procPath -OutputDir $outDir -SourceHeight $height
        
        # 2. 生成封面
        Write-Log "[2/4] 生成封面..." "Yellow"
        $coversDir = New-VideoCovers -VideoPath $procPath -OutputDir $outDir -Duration $duration
        $bestCover = Get-BestCover -CoversDir $coversDir
        
        # 3. 生成预览
        Write-Log "[3/4] 生成预览..." "Yellow"
        $previewPath = Join-Path $outDir "${name}_preview.webm"
        # 简化预览生成
        $previewPos = $duration * 0.3
        & ffmpeg -ss $previewPos -i $procPath -t 10 -c:v libvpx-vp9 -b:v 500k -vf "scale=480:-1" -an -y $previewPath 2>&1 | Out-Null
        
        # 4. 上传到主服务器
        Write-Log "[4/4] 上传到主服务器..." "Yellow"
        
        # 使用视频ID作为远程目录名
        $videoId = Get-Date -Format "yyyyMMddHHmmss"
        $remoteHlsDir = "/www/wwwroot/video-app/backend/uploads/hls/$videoId"
        
        # 上传HLS目录
        Write-Log "  上传HLS目录..." "Gray"
        Upload-Directory -LocalDir $hlsDir -RemoteDir $remoteHlsDir
        
        # 上传封面目录
        Write-Log "  上传封面目录..." "Gray"
        Upload-Directory -LocalDir $coversDir -RemoteDir "$remoteHlsDir/covers"
        
        # 上传预览
        if (Test-Path $previewPath) {
            Upload-SingleFile -LocalPath $previewPath -RemotePath "/www/wwwroot/video-app/backend/uploads/previews/"
        }
        
        # 设置权限
        & ssh -i $config.SshKey -o StrictHostKeyChecking=no "root@$($config.MainServer)" "chown -R www:www $remoteHlsDir" 2>&1 | Out-Null
        
        # 发送回调
        Write-Log "  发送回调..." "Yellow"
        $hlsUrl = "/uploads/hls/$videoId/master.m3u8"
        $coverUrl = "/uploads/hls/$videoId/covers/cover_$bestCover.webp"
        $previewUrl = "/uploads/previews/${name}_preview.webm"
        
        Send-Callback -Filename $name -Title $name -IsShort $false `
            -HlsUrl $hlsUrl -CoverUrl $coverUrl -PreviewUrl $previewUrl -Duration $duration
        
        # 清理
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        
        Write-Log "长视频处理完成: $name" "Green"
        return $true
        
    } catch {
        Write-Log "处理异常: $_" "Red"
        if (Test-Path $procPath) {
            Move-Item -LiteralPath $procPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# ========== 处理短视频 ==========
function Process-ShortVideo {
    param([System.IO.FileInfo]$VideoFile)
    
    $name = [System.IO.Path]::GetFileNameWithoutExtension($VideoFile.Name)
    $outDir = Join-Path $config.BaseDir "completed\short\$name"
    $procPath = Join-Path $config.BaseDir "processing\$($VideoFile.Name)"
    
    Write-Log "==========================================" "Cyan"
    Write-Log "处理短视频: $($VideoFile.Name)" "Cyan"
    Write-Log "==========================================" "Cyan"
    
    try {
        Move-Item -LiteralPath $VideoFile.FullName -Destination $procPath -Force
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        $duration = Get-VideoDuration -VideoPath $procPath
        
        # 1. 转码
        Write-Log "[1/3] 转码..." "Yellow"
        $outVideo = Join-Path $outDir "$name.mp4"
        & ffmpeg -i $procPath -c:v libx264 -preset fast -crf 23 -vf "scale=-2:720" -c:a aac -b:a 128k -movflags +faststart -y $outVideo 2>&1 | Out-Null
        
        # 2. 生成封面
        Write-Log "[2/3] 生成封面..." "Yellow"
        $coversDir = New-VideoCovers -VideoPath $outVideo -OutputDir $outDir -Duration $duration
        $bestCover = Get-BestCover -CoversDir $coversDir
        $mainCover = Join-Path $outDir "$name.webp"
        Copy-Item (Join-Path $coversDir "cover_$bestCover.webp") $mainCover -Force
        
        # 3. 上传
        Write-Log "[3/3] 上传..." "Yellow"
        Upload-SingleFile -LocalPath $outVideo -RemotePath "/www/wwwroot/video-app/backend/uploads/shorts/"
        Upload-SingleFile -LocalPath $mainCover -RemotePath "/www/wwwroot/video-app/backend/uploads/thumbnails/"
        
        # 上传封面目录（用于后台选择）
        $remoteCoversDir = "/www/wwwroot/video-app/backend/uploads/shorts/thumbnails/$name"
        Upload-Directory -LocalDir $coversDir -RemoteDir $remoteCoversDir
        
        # 回调
        $videoUrl = "/uploads/shorts/$name.mp4"
        $coverUrl = "/uploads/thumbnails/$name.webp"
        
        Send-Callback -Filename $name -Title $name -IsShort $true `
            -VideoUrl $videoUrl -CoverUrl $coverUrl -Duration $duration
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        
        Write-Log "短视频处理完成: $name" "Green"
        return $true
        
    } catch {
        Write-Log "处理异常: $_" "Red"
        if (Test-Path $procPath) {
            Move-Item -LiteralPath $procPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# ========== 主循环 ==========
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  视频处理监控服务 (完整版)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "长视频目录: $($config.BaseDir)\downloads\long" -ForegroundColor White
Write-Host "短视频目录: $($config.BaseDir)\downloads\short" -ForegroundColor White
Write-Host "日志文件: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "功能: 转码 → 生成封面(10张) → 生成HLS → 上传 → 回调" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

Write-Log "=== 监控服务启动 ===" "Green"

$stats = @{ Processed = 0; Failed = 0; StartTime = Get-Date }

while ($true) {
    try {
        # 处理长视频
        $longVideos = Get-ChildItem -LiteralPath "$($config.BaseDir)\downloads\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
        foreach ($video in $longVideos) {
            $initialSize = $video.Length
            Start-Sleep -Seconds 2
            $video.Refresh()
            if ($video.Length -ne $initialSize) {
                Write-Log "文件正在写入，跳过: $($video.Name)" "Gray"
                continue
            }
            
            if (Process-LongVideo -VideoFile $video) {
                $stats.Processed++
            } else {
                $stats.Failed++
            }
        }
        
        # 处理短视频
        $shortVideos = Get-ChildItem -LiteralPath "$($config.BaseDir)\downloads\short" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
        foreach ($video in $shortVideos) {
            $initialSize = $video.Length
            Start-Sleep -Seconds 2
            $video.Refresh()
            if ($video.Length -ne $initialSize) {
                Write-Log "文件正在写入，跳过: $($video.Name)" "Gray"
                continue
            }
            
            if (Process-ShortVideo -VideoFile $video) {
                $stats.Processed++
            } else {
                $stats.Failed++
            }
        }
        
        Start-Sleep -Seconds $config.CheckInterval
        
    } catch {
        Write-Log "监控循环异常: $_" "Red"
        Start-Sleep -Seconds 30
    }
}
