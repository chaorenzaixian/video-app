# watcher.ps1 - Video Processing Monitor Service
# Features: Monitor download directory, auto transcode -> covers -> HLS -> upload -> callback
# Supports: Long videos (HLS multi-resolution) and Short videos (single file)
# Deploy: D:\VideoTranscode\scripts\watcher.ps1

$ErrorActionPreference = "Continue"

# ========== Lock File for Guardian ==========
$lockFile = "D:\VideoTranscode\watcher.lock"
$PID | Out-File -FilePath $lockFile -Force -Encoding ASCII

$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Remove-Item "D:\VideoTranscode\watcher.lock" -Force -ErrorAction SilentlyContinue
}

# ========== Config ==========
$config = @{
    BaseDir = "D:\VideoTranscode"
    MainServer = "38.47.218.137"
    SshKey = "C:\server_key"
    TranscodeKey = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"
    ApiBase = "http://38.47.218.137:8000/api/v1"
    CheckInterval = 10
}

$logFile = "$($config.BaseDir)\logs\watcher_$(Get-Date -Format 'yyyyMMdd').log"

# Ensure directories exist
@("downloads\long", "downloads\short", "processing", "completed\long", "completed\short", "logs") | ForEach-Object {
    $dir = Join-Path $config.BaseDir $_
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

# ========== Utility Functions ==========
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
        # Handle array result (take first value)
        if ($result -is [array]) { $result = $result[0] }
        $duration = [double]$result
        if ($duration -gt 0) { return $duration }
        return 60
    } catch { return 60 }
}

function Get-VideoHeight {
    param([string]$VideoPath)
    try {
        $result = & ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 $VideoPath 2>$null
        # Handle array result (take first value)
        if ($result -is [array]) { $result = $result[0] }
        $height = [int]$result
        if ($height -gt 0) { return $height }
        return 720
    } catch { return 720 }
}

# ========== Upload Functions ==========
function Upload-SingleFile {
    param([string]$LocalPath, [string]$RemotePath)
    
    if (-not (Test-Path -LiteralPath $LocalPath)) {
        Write-Log "  Upload skip: file not found $LocalPath" "Yellow"
        return $false
    }
    
    $fileName = [System.IO.Path]::GetFileName($LocalPath)
    $fileSize = [math]::Round((Get-Item -LiteralPath $LocalPath).Length / 1MB, 2)
    
    Write-Log "  Upload: $fileName (${fileSize}MB)" "Gray"
    
    & scp -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $LocalPath "root@$($config.MainServer):$RemotePath" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "  Success: $fileName" "Green"
        return $true
    } else {
        Write-Log "  Failed: $fileName" "Red"
        return $false
    }
}

function Upload-Directory {
    param([string]$LocalDir, [string]$RemoteDir)
    
    if (-not (Test-Path -LiteralPath $LocalDir)) {
        Write-Log "  Upload skip: dir not found $LocalDir" "Yellow"
        return $false
    }
    
    & ssh -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$($config.MainServer)" "mkdir -p `"$RemoteDir`"" 2>&1 | Out-Null
    
    $files = Get-ChildItem -LiteralPath $LocalDir -File -Recurse
    $uploadCount = 0
    
    foreach ($f in $files) {
        $relativePath = $f.FullName.Substring($LocalDir.Length + 1).Replace('\', '/')
        $remoteFile = "$RemoteDir/$relativePath"
        $remoteFileDir = [System.IO.Path]::GetDirectoryName($remoteFile).Replace('\', '/')
        
        & ssh -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "root@$($config.MainServer)" "mkdir -p `"$remoteFileDir`"" 2>&1 | Out-Null
        & scp -i $config.SshKey -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL $f.FullName "root@$($config.MainServer):$remoteFile" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) { $uploadCount++ }
    }
    
    Write-Log "  Dir upload done: $uploadCount/$($files.Count) files" "Green"
    return $uploadCount -gt 0
}

# ========== Cover Generation ==========
function New-VideoCovers {
    param([string]$VideoPath, [string]$OutputDir, [double]$Duration, [int]$Count = 10)
    
    $coversDir = Join-Path $OutputDir "covers"
    if (-not (Test-Path $coversDir)) { New-Item -ItemType Directory -Path $coversDir -Force | Out-Null }
    
    Write-Log "  Generating $Count covers..." "Yellow"
    
    for ($i = 1; $i -le $Count; $i++) {
        $position = $Duration * ($i / ($Count + 1))
        $coverPath = Join-Path $coversDir "cover_$i.webp"
        
        & ffmpeg -ss $position -i $VideoPath -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y $coverPath 2>&1 | Out-Null
    }
    
    $generatedCount = (Get-ChildItem -Path $coversDir -Filter "cover_*.webp" -ErrorAction SilentlyContinue).Count
    Write-Log "  Covers done: $generatedCount" "Green"
    
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

# ========== FFmpeg with Progress ==========
function Invoke-FFmpegWithProgress {
    param(
        [string]$Arguments,
        [double]$Duration,
        [string]$TaskName
    )
    
    $progressFile = Join-Path $env:TEMP "ffmpeg_progress_$([guid]::NewGuid().ToString('N').Substring(0,8)).txt"
    $fullArgs = "-progress `"$progressFile`" -y $Arguments"
    
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $fullArgs -NoNewWindow -PassThru -RedirectStandardError "NUL"
    
    $lastPercent = -1
    while (-not $process.HasExited) {
        Start-Sleep -Milliseconds 500
        
        if (Test-Path $progressFile) {
            $content = Get-Content $progressFile -Raw -ErrorAction SilentlyContinue
            if ($content -match "out_time_ms=(\d+)") {
                $currentMs = [long]$matches[1]
                $currentSec = $currentMs / 1000000
                $percent = [math]::Min(100, [math]::Round(($currentSec / $Duration) * 100, 1))
                
                if ($percent -ne $lastPercent -and $percent % 5 -eq 0) {
                    Write-Host "`r    $TaskName : $percent%" -NoNewline -ForegroundColor Cyan
                    $lastPercent = $percent
                }
            }
        }
    }
    
    Write-Host "`r    $TaskName : 100%    " -ForegroundColor Green
    
    Remove-Item $progressFile -Force -ErrorAction SilentlyContinue
    
    return $process.ExitCode -eq 0
}

# ========== HLS Generation ==========
function New-HlsStream {
    param([string]$VideoPath, [string]$OutputDir, [int]$SourceHeight, [double]$Duration = 0)
    
    $hlsDir = Join-Path $OutputDir "hls"
    if (-not (Test-Path $hlsDir)) { New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null }
    
    Write-Log "  Generating HLS (source: ${SourceHeight}p, single resolution mode)..." "Yellow"
    
    # Only use source resolution - no downscaling
    $resName = "${SourceHeight}p"
    $bitrate = switch ($SourceHeight) {
        { $_ -ge 1080 } { "4000k" }
        { $_ -ge 720 } { "2500k" }
        { $_ -ge 480 } { "1200k" }
        default { "800k" }
    }
    
    $resDir = Join-Path $hlsDir $resName
    if (-not (Test-Path $resDir)) { New-Item -ItemType Directory -Path $resDir -Force | Out-Null }
    
    $playlistPath = Join-Path $resDir "playlist.m3u8"
    $segmentPattern = Join-Path $resDir "seg_%03d.ts"
    
    Write-Log "    Generating $resName..." "Gray"
    
    # Use copy codec if possible for faster processing, otherwise re-encode
    $ffmpegArgs = "-i `"$VideoPath`" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k -f hls -hls_time 10 -hls_list_size 0 -hls_segment_filename `"$segmentPattern`" `"$playlistPath`""
    
    if ($Duration -gt 0) {
        Invoke-FFmpegWithProgress -Arguments $ffmpegArgs -Duration $Duration -TaskName "$resName"
    } else {
        & ffmpeg -i $VideoPath -c:v libx264 -preset fast -crf 23 `
            -c:a aac -b:a 128k `
            -f hls -hls_time 10 -hls_list_size 0 `
            -hls_segment_filename $segmentPattern `
            -y $playlistPath 2>&1 | Out-Null
    }
    
    # Create master.m3u8 with single resolution
    $masterPath = Join-Path $hlsDir "master.m3u8"
    $bandwidth = [int]($bitrate.Replace("k", "")) * 1000
    $width = [int]($SourceHeight * 16 / 9)
    $masterContent = "#EXTM3U`n#EXT-X-VERSION:3`n#EXT-X-STREAM-INF:BANDWIDTH=$bandwidth,RESOLUTION=${width}x$SourceHeight`n$resName/playlist.m3u8`n"
    
    $masterContent | Out-File -FilePath $masterPath -Encoding UTF8 -NoNewline
    
    Write-Log "  HLS done: $resName only (fast mode)" "Green"
    
    return $hlsDir
}

# ========== API Callback ==========
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
        
        Write-Log "  Callback success: $result" "Green"
        return $true
    } catch {
        Write-Log "  Callback failed: $_" "Red"
        return $false
    }
}

# ========== Process Long Video ==========
function Process-LongVideo {
    param([System.IO.FileInfo]$VideoFile)
    
    $name = [System.IO.Path]::GetFileNameWithoutExtension($VideoFile.Name)
    $outDir = Join-Path $config.BaseDir "completed\long\$name"
    $procPath = Join-Path $config.BaseDir "processing\$($VideoFile.Name)"
    
    Write-Log "==========================================" "Cyan"
    Write-Log "Processing Long Video: $($VideoFile.Name)" "Cyan"
    Write-Log "==========================================" "Cyan"
    
    try {
        Move-Item -LiteralPath $VideoFile.FullName -Destination $procPath -Force
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        $duration = Get-VideoDuration -VideoPath $procPath
        $height = Get-VideoHeight -VideoPath $procPath
        Write-Log "  Video info: duration=${duration}s, height=${height}p" "White"
        
        Write-Log "[1/4] Generating HLS..." "Yellow"
        $hlsDir = New-HlsStream -VideoPath $procPath -OutputDir $outDir -SourceHeight $height -Duration $duration
        
        Write-Log "[2/4] Generating covers..." "Yellow"
        $coversDir = New-VideoCovers -VideoPath $procPath -OutputDir $outDir -Duration $duration
        $bestCover = Get-BestCover -CoversDir $coversDir
        
        Write-Log "[3/4] Generating preview..." "Yellow"
        $previewPath = Join-Path $outDir "${name}_preview.webm"
        $previewPos = $duration * 0.3
        & ffmpeg -ss $previewPos -i $procPath -t 10 -c:v libvpx-vp9 -b:v 500k -vf "scale=480:-1" -an -y $previewPath 2>&1 | Out-Null
        
        Write-Log "[4/4] Uploading to main server..." "Yellow"
        
        $videoId = Get-Date -Format "yyyyMMddHHmmss"
        $remoteHlsDir = "/www/wwwroot/video-app/backend/uploads/hls/$videoId"
        
        Write-Log "  Uploading HLS..." "Gray"
        Upload-Directory -LocalDir $hlsDir -RemoteDir $remoteHlsDir
        
        Write-Log "  Uploading covers..." "Gray"
        Upload-Directory -LocalDir $coversDir -RemoteDir "$remoteHlsDir/covers"
        
        if (Test-Path $previewPath) {
            Upload-SingleFile -LocalPath $previewPath -RemotePath "/www/wwwroot/video-app/backend/uploads/previews/"
        }
        
        & ssh -i $config.SshKey -o StrictHostKeyChecking=no "root@$($config.MainServer)" "chown -R www:www $remoteHlsDir" 2>&1 | Out-Null
        
        Write-Log "  Sending callback..." "Yellow"
        $hlsUrl = "/uploads/hls/$videoId/master.m3u8"
        $coverUrl = "/uploads/hls/$videoId/covers/cover_$bestCover.webp"
        $previewUrl = "/uploads/previews/${name}_preview.webm"
        
        Send-Callback -Filename $name -Title $name -IsShort $false `
            -HlsUrl $hlsUrl -CoverUrl $coverUrl -PreviewUrl $previewUrl -Duration $duration
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        
        Write-Log "Long video done: $name" "Green"
        return $true
        
    } catch {
        Write-Log "Process error: $_" "Red"
        if (Test-Path $procPath) {
            Move-Item -LiteralPath $procPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# ========== Process Short Video (HLS mode) ==========
function Process-ShortVideo {
    param([System.IO.FileInfo]$VideoFile)
    
    $name = [System.IO.Path]::GetFileNameWithoutExtension($VideoFile.Name)
    $outDir = Join-Path $config.BaseDir "completed\short\$name"
    $procPath = Join-Path $config.BaseDir "processing\$($VideoFile.Name)"
    
    Write-Log "==========================================" "Cyan"
    Write-Log "Processing Short Video (HLS): $($VideoFile.Name)" "Cyan"
    Write-Log "==========================================" "Cyan"
    
    try {
        Move-Item -LiteralPath $VideoFile.FullName -Destination $procPath -Force
        if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
        
        $duration = Get-VideoDuration -VideoPath $procPath
        $height = Get-VideoHeight -VideoPath $procPath
        Write-Log "  Video info: duration=${duration}s, height=${height}p" "White"
        
        Write-Log "[1/3] Generating HLS..." "Yellow"
        $hlsDir = New-HlsStream -VideoPath $procPath -OutputDir $outDir -SourceHeight $height -Duration $duration
        
        Write-Log "[2/3] Generating covers..." "Yellow"
        $coversDir = New-VideoCovers -VideoPath $procPath -OutputDir $outDir -Duration $duration
        $bestCover = Get-BestCover -CoversDir $coversDir
        
        Write-Log "[3/3] Uploading to main server..." "Yellow"
        
        $videoId = "short_$(Get-Date -Format 'yyyyMMddHHmmss')"
        $remoteHlsDir = "/www/wwwroot/video-app/backend/uploads/hls/$videoId"
        
        Write-Log "  Uploading HLS..." "Gray"
        Upload-Directory -LocalDir $hlsDir -RemoteDir $remoteHlsDir
        
        Write-Log "  Uploading covers..." "Gray"
        Upload-Directory -LocalDir $coversDir -RemoteDir "$remoteHlsDir/covers"
        
        & ssh -i $config.SshKey -o StrictHostKeyChecking=no "root@$($config.MainServer)" "chown -R www:www $remoteHlsDir" 2>&1 | Out-Null
        
        Write-Log "  Sending callback..." "Yellow"
        $hlsUrl = "/uploads/hls/$videoId/master.m3u8"
        $coverUrl = "/uploads/hls/$videoId/covers/cover_$bestCover.webp"
        
        Send-Callback -Filename $name -Title $name -IsShort $true `
            -HlsUrl $hlsUrl -CoverUrl $coverUrl -Duration $duration
        
        Remove-Item -LiteralPath $procPath -Force -ErrorAction SilentlyContinue
        
        Write-Log "Short video done (HLS): $name" "Green"
        return $true
        
    } catch {
        Write-Log "Process error: $_" "Red"
        if (Test-Path $procPath) {
            Move-Item -LiteralPath $procPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
}

# ========== Main Loop ==========
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Video Processing Monitor Service" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Long video dir: $($config.BaseDir)\downloads\long" -ForegroundColor White
Write-Host "Short video dir: $($config.BaseDir)\downloads\short" -ForegroundColor White
Write-Host "Log file: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "Features: Transcode -> Covers(10) -> HLS -> Upload -> Callback" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

Write-Log "=== Monitor Service Started ===" "Green"

$stats = @{ Processed = 0; Failed = 0; StartTime = Get-Date }

while ($true) {
    try {
        # Process long videos
        $longVideos = Get-ChildItem -LiteralPath "$($config.BaseDir)\downloads\long" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
        foreach ($video in $longVideos) {
            $initialSize = $video.Length
            Start-Sleep -Seconds 2
            $video.Refresh()
            if ($video.Length -ne $initialSize) {
                Write-Log "File still writing, skip: $($video.Name)" "Gray"
                continue
            }
            
            if (Process-LongVideo -VideoFile $video) {
                $stats.Processed++
            } else {
                $stats.Failed++
            }
        }
        
        # Process short videos
        $shortVideos = Get-ChildItem -LiteralPath "$($config.BaseDir)\downloads\short" -Filter "*.mp4" -File -ErrorAction SilentlyContinue
        foreach ($video in $shortVideos) {
            $initialSize = $video.Length
            Start-Sleep -Seconds 2
            $video.Refresh()
            if ($video.Length -ne $initialSize) {
                Write-Log "File still writing, skip: $($video.Name)" "Gray"
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
        Write-Log "Monitor loop error: $_" "Red"
        Start-Sleep -Seconds 30
    }
}
