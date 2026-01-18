# transcode_v2.ps1 - 视频转码脚本 v2
# 短视频: MP4 (720p) + 多封面
# 长视频: HLS 多码率 (720p/480p/360p) + 多封面 + 预览
# 部署到: D:\VideoTranscode\scripts\transcode_v2.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputDir,
    
    [Parameter(Mandatory=$true)]
    [ValidateSet("short", "long")]
    [string]$VideoType,
    
    [string]$VideoId = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = "D:\VideoTranscode\logs"
$logFile = "$logDir\transcode.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append -Encoding UTF8
    Write-Host "$timestamp - $Message"
}

function Get-VideoDuration {
    param([string]$VideoPath)
    try {
        $result = & ffprobe -v error -show_entries format=duration -of csv=p=0 $VideoPath 2>$null
        return [double]$result
    } catch {
        return 60.0
    }
}

function Get-VideoResolution {
    param([string]$VideoPath)
    try {
        $width = & ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 $VideoPath 2>$null
        $height = & ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 $VideoPath 2>$null
        return @{ Width = [int]$width; Height = [int]$height }
    } catch {
        return @{ Width = 1280; Height = 720 }
    }
}


# ========== 智能封面评分 ==========
function Get-FrameScore {
    param([string]$ImagePath)
    
    # 使用 FFmpeg 获取图片统计信息
    try {
        $stats = & ffprobe -v error -select_streams v:0 -show_entries frame=pkt_pts_time -show_frames -of csv=p=0 $ImagePath 2>$null
        
        # 简单评分: 基于文件大小 (越大通常越丰富)
        $fileSize = (Get-Item $ImagePath).Length
        $score = $fileSize / 1024  # KB
        
        # 避免过小的图片 (可能是黑帧)
        if ($score -lt 5) { $score = 0 }
        
        return $score
    } catch {
        return 50  # 默认分数
    }
}

# ========== 生成多张候选封面 ==========
function New-MultipleCovers {
    param(
        [string]$Input,
        [string]$OutputDir,
        [string]$BaseName,
        [double]$Duration,
        [int]$Count = 10
    )
    
    Write-Log "[封面] 生成 $Count 张候选封面..."
    
    $coversDir = Join-Path $OutputDir "covers"
    if (-not (Test-Path $coversDir)) {
        New-Item -ItemType Directory -Path $coversDir -Force | Out-Null
    }
    
    $covers = @()
    $tempCovers = @()
    
    # 均匀分布截取帧
    for ($i = 0; $i -lt $Count; $i++) {
        $position = 0.1 + (0.8 * $i / ($Count - 1))
        $seekTime = $Duration * $position
        
        $tempPath = Join-Path $coversDir "temp_$i.png"
        $tempCovers += $tempPath
        
        $ffmpegArgs = @(
            "-ss", $seekTime.ToString("F2"),
            "-i", $Input,
            "-vframes", "1",
            "-vf", "scale=640:-1",
            "-y",
            $tempPath
        )
        
        & ffmpeg @ffmpegArgs 2>$null
    }
    
    # 评分并排序
    $scoredCovers = @()
    foreach ($tempPath in $tempCovers) {
        if (Test-Path $tempPath) {
            $score = Get-FrameScore -ImagePath $tempPath
            $scoredCovers += @{ Path = $tempPath; Score = $score }
        }
    }
    
    $scoredCovers = $scoredCovers | Sort-Object -Property Score -Descending
    
    # 转换为 WebP 并保存
    $rank = 1
    foreach ($item in $scoredCovers) {
        $outputPath = Join-Path $coversDir "${BaseName}_cover_$rank.webp"
        
        $ffmpegArgs = @(
            "-i", $item.Path,
            "-c:v", "libwebp",
            "-quality", "85",
            "-y",
            $outputPath
        )
        
        & ffmpeg @ffmpegArgs 2>$null
        
        if (Test-Path $outputPath) {
            $covers += $outputPath
            Write-Log "  封面 $rank : score=$([math]::Round($item.Score, 1))"
        }
        
        # 删除临时文件
        Remove-Item $item.Path -Force -ErrorAction SilentlyContinue
        
        $rank++
    }
    
    # 复制最佳封面为主封面
    if ($covers.Count -gt 0) {
        $mainCover = Join-Path $OutputDir "${BaseName}.webp"
        Copy-Item $covers[0] $mainCover -Force
        Write-Log "[封面] 主封面: ${BaseName}.webp"
    }
    
    Write-Log "[封面] 完成! 生成 $($covers.Count) 张封面"
    return $covers
}


# ========== 短视频转码 (MP4 720p) ==========
function Start-ShortVideoTranscode {
    param(
        [string]$Input,
        [string]$Output
    )
    
    Write-Log "[短视频] 开始转码..."
    
    # 检测 GPU
    $hasNvenc = $false
    try {
        $nvencTest = & ffmpeg -hide_banner -encoders 2>&1 | Select-String "h264_nvenc"
        if ($nvencTest) { $hasNvenc = $true }
    } catch {}
    
    if ($hasNvenc) {
        Write-Log "[短视频] 使用 GPU 加速"
        $ffmpegArgs = @(
            "-hwaccel", "cuda",
            "-i", $Input,
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "23",
            "-vf", "scale=-2:720",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            $Output
        )
    } else {
        Write-Log "[短视频] 使用 CPU 转码"
        $ffmpegArgs = @(
            "-i", $Input,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-vf", "scale=-2:720",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            $Output
        )
    }
    
    $startTime = Get-Date
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    
    if ($process.ExitCode -eq 0 -and (Test-Path $Output)) {
        $size = [math]::Round((Get-Item $Output).Length / 1MB, 2)
        Write-Log "[短视频] 完成! 耗时: ${elapsed}秒, 大小: ${size}MB"
        return $true
    } else {
        Write-Log "[短视频] 失败!"
        return $false
    }
}

# ========== 长视频转码 (HLS 多码率) ==========
function Start-LongVideoTranscode {
    param(
        [string]$Input,
        [string]$OutputDir,
        [string]$BaseName
    )
    
    Write-Log "[长视频] 开始 HLS 多码率转码..."
    
    $hlsDir = Join-Path $OutputDir "hls"
    if (-not (Test-Path $hlsDir)) {
        New-Item -ItemType Directory -Path $hlsDir -Force | Out-Null
    }
    
    # 创建各码率目录
    $resolutions = @(
        @{ Name = "720p"; Height = 720; Bitrate = "2500k"; AudioBitrate = "128k" },
        @{ Name = "480p"; Height = 480; Bitrate = "1500k"; AudioBitrate = "96k" },
        @{ Name = "360p"; Height = 360; Bitrate = "800k"; AudioBitrate = "64k" }
    )
    
    $playlists = @()
    
    foreach ($res in $resolutions) {
        $resDir = Join-Path $hlsDir $res.Name
        if (-not (Test-Path $resDir)) {
            New-Item -ItemType Directory -Path $resDir -Force | Out-Null
        }
        
        $playlistPath = Join-Path $resDir "playlist.m3u8"
        $segmentPath = Join-Path $resDir "segment_%03d.ts"
        
        Write-Log "  转码 $($res.Name)..."
        
        $ffmpegArgs = @(
            "-i", $Input,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-vf", "scale=-2:$($res.Height)",
            "-c:a", "aac",
            "-b:a", $res.AudioBitrate,
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_segment_filename", $segmentPath,
            "-y",
            $playlistPath
        )
        
        $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            $playlists += @{
                Name = $res.Name
                Bandwidth = [int]($res.Bitrate.Replace("k", "")) * 1000
                Path = "$($res.Name)/playlist.m3u8"
            }
            Write-Log "  $($res.Name) 完成!"
        }
    }
    
    # 生成主播放列表
    $masterPlaylist = Join-Path $hlsDir "master.m3u8"
    $masterContent = "#EXTM3U`n#EXT-X-VERSION:3`n"
    
    foreach ($pl in $playlists) {
        $masterContent += "#EXT-X-STREAM-INF:BANDWIDTH=$($pl.Bandwidth),RESOLUTION=$($pl.Name)`n"
        $masterContent += "$($pl.Path)`n"
    }
    
    $masterContent | Out-File -FilePath $masterPlaylist -Encoding UTF8 -NoNewline
    
    Write-Log "[长视频] HLS 转码完成! 生成 $($playlists.Count) 个码率"
    return $playlists.Count -gt 0
}


# ========== 长视频预览 ==========
function New-VideoPreview {
    param(
        [string]$Input,
        [string]$Output,
        [double]$Duration
    )
    
    Write-Log "[预览] 生成预览视频..."
    
    $numSegments = 10
    $segDuration = 1.0
    
    if ($Duration -lt 10) {
        $numSegments = [math]::Max(1, [int]$Duration)
    }
    
    $tempDir = Split-Path $Output -Parent
    $tempFiles = @()
    
    for ($i = 0; $i -lt $numSegments; $i++) {
        if ($numSegments -gt 1) {
            $position = 0.05 + (0.9 * $i / ($numSegments - 1))
        } else {
            $position = 0.5
        }
        $startTime = $Duration * $position
        
        $tempPath = Join-Path $tempDir "temp_seg_$i.webm"
        $tempFiles += $tempPath
        
        $ffmpegArgs = @(
            "-ss", $startTime.ToString("F2"),
            "-i", $Input,
            "-t", $segDuration.ToString("F2"),
            "-c:v", "libvpx-vp9",
            "-b:v", "500k",
            "-vf", "scale=480:-1",
            "-an",
            "-y",
            $tempPath
        )
        
        & ffmpeg @ffmpegArgs 2>$null
    }
    
    # 拼接
    $concatFile = Join-Path $tempDir "concat_list.txt"
    $concatContent = ""
    foreach ($tempPath in $tempFiles) {
        if (Test-Path $tempPath) {
            $safePath = $tempPath.Replace('\', '/')
            $concatContent += "file '$safePath'`n"
        }
    }
    $concatContent | Out-File -FilePath $concatFile -Encoding UTF8 -NoNewline
    
    $concatArgs = @(
        "-f", "concat",
        "-safe", "0",
        "-i", $concatFile,
        "-c:v", "libvpx-vp9",
        "-b:v", "500k",
        "-y",
        $Output
    )
    
    & ffmpeg @concatArgs 2>$null
    
    # 清理
    foreach ($tempPath in $tempFiles) {
        Remove-Item $tempPath -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $concatFile -Force -ErrorAction SilentlyContinue
    
    if (Test-Path $Output) {
        $size = [math]::Round((Get-Item $Output).Length / 1KB, 1)
        Write-Log "[预览] 完成! 大小: ${size}KB"
        return $true
    }
    return $false
}

# ========== 主流程 ==========
Write-Log "=========================================="
Write-Log "开始处理: $InputFile"
Write-Log "类型: $VideoType"
Write-Log "=========================================="

if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Log "错误: 输入文件不存在"
    exit 1
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$baseName = if ($VideoId) { $VideoId } else { [System.IO.Path]::GetFileNameWithoutExtension($InputFile) }
$duration = Get-VideoDuration -VideoPath $InputFile
$resolution = Get-VideoResolution -VideoPath $InputFile

Write-Log "视频信息: 时长=${duration}秒, 分辨率=$($resolution.Width)x$($resolution.Height)"

$result = @{
    success = $false
    type = $VideoType
    video = $null
    hls = $null
    covers = @()
    preview = $null
    duration = $duration
}

# 根据类型处理
if ($VideoType -eq "short") {
    # 短视频: MP4 + 多封面
    $videoOutput = Join-Path $OutputDir "${baseName}.mp4"
    
    $transcodeSuccess = Start-ShortVideoTranscode -Input $InputFile -Output $videoOutput
    
    if ($transcodeSuccess) {
        $result.video = $videoOutput
        $result.covers = New-MultipleCovers -Input $videoOutput -OutputDir $OutputDir -BaseName $baseName -Duration $duration
        $result.success = $true
    }
} else {
    # 长视频: HLS + 多封面 + 预览
    $hlsSuccess = Start-LongVideoTranscode -Input $InputFile -OutputDir $OutputDir -BaseName $baseName
    
    if ($hlsSuccess) {
        $result.hls = Join-Path $OutputDir "hls\master.m3u8"
        $result.covers = New-MultipleCovers -Input $InputFile -OutputDir $OutputDir -BaseName $baseName -Duration $duration
        
        $previewOutput = Join-Path $OutputDir "${baseName}_preview.webm"
        $previewSuccess = New-VideoPreview -Input $InputFile -Output $previewOutput -Duration $duration
        if ($previewSuccess) {
            $result.preview = $previewOutput
        }
        
        $result.success = $true
    }
}

Write-Log "=========================================="
Write-Log "处理完成!"
Write-Log "=========================================="

$result | ConvertTo-Json -Depth 3 | Write-Output

exit 0
