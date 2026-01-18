# transcode_full.ps1 - 完整视频处理脚本（转码+封面+预览）
# 部署到转码服务器: D:\VideoTranscode\scripts\transcode_full.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputDir,  # 输出目录，会在此目录下生成 video.mp4, cover.webp, preview.mp4
    
    [string]$VideoId = ""  # 可选的视频ID，用于命名
)

$ErrorActionPreference = "Stop"
$logDir = "D:\VideoTranscode\logs"
$logFile = "$logDir\transcode_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# 确保日志目录存在
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append
    Write-Host $logMessage -ForegroundColor $Color
}

function Get-VideoDuration {
    param([string]$VideoPath)
    
    $ffprobeArgs = @(
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        $VideoPath
    )
    
    try {
        $result = & ffprobe @ffprobeArgs 2>$null
        return [double]$result
    } catch {
        return 60.0  # 默认60秒
    }
}

function Get-VideoHeight {
    param([string]$VideoPath)
    
    $ffprobeArgs = @(
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=height",
        "-of", "csv=p=0",
        $VideoPath
    )
    
    try {
        $result = & ffprobe @ffprobeArgs 2>$null
        return [int]$result
    } catch {
        return 720  # 默认720p
    }
}

# ========== 1. 转码视频 ==========
function Start-VideoTranscode {
    param(
        [string]$Input,
        [string]$Output
    )
    
    Write-Log "[转码] 开始转码视频..." "Yellow"
    
    # 检测是否有NVIDIA GPU
    $hasNvenc = $false
    try {
        $nvencTest = & ffmpeg -hide_banner -encoders 2>&1 | Select-String "h264_nvenc"
        if ($nvencTest) { $hasNvenc = $true }
    } catch {}
    
    if ($hasNvenc) {
        Write-Log "[转码] 使用GPU加速 (NVENC)" "Cyan"
        $ffmpegArgs = @(
            "-hwaccel", "cuda",
            "-i", $Input,
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            $Output
        )
    } else {
        Write-Log "[转码] 使用CPU转码" "Cyan"
        $ffmpegArgs = @(
            "-i", $Input,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-y",
            $Output
        )
    }
    
    $startTime = Get-Date
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($process.ExitCode -eq 0 -and (Test-Path $Output)) {
        $fileSize = (Get-Item $Output).Length / 1MB
        $roundedDuration = [math]::Round($duration, 1)
        $roundedSize = [math]::Round($fileSize, 2)
        Write-Log "[转码] 完成! 耗时: ${roundedDuration}秒, 大小: ${roundedSize}MB" "Green"
        return $true
    } else {
        Write-Log "[转码] 失败! 退出码: $($process.ExitCode)" "Red"
        return $false
    }
}

# ========== 2. 生成封面 ==========
function New-VideoCover {
    param(
        [string]$Input,
        [string]$Output,
        [double]$Duration
    )
    
    Write-Log "[封面] 开始生成封面..." "Yellow"
    
    # 在视频30%位置截图（避开片头）
    $seekTime = $Duration * 0.3
    if ($seekTime -lt 1) { $seekTime = 1 }
    if ($seekTime -gt $Duration - 1) { $seekTime = $Duration / 2 }
    
    $ffmpegArgs = @(
        "-ss", $seekTime.ToString("F2"),
        "-i", $Input,
        "-vframes", "1",
        "-vf", "scale=640:-1",
        "-c:v", "libwebp",
        "-quality", "85",
        "-y",
        $Output
    )
    
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
    
    if ($process.ExitCode -eq 0 -and (Test-Path $Output)) {
        $fileSize = (Get-Item $Output).Length / 1KB
        $roundedSize = [math]::Round($fileSize, 1)
        Write-Log "[封面] 完成! 大小: ${roundedSize}KB" "Green"
        return $true
    } else {
        Write-Log "[封面] 失败!" "Red"
        return $false
    }
}

# ========== 3. 生成预览 ==========
function New-VideoPreview {
    param(
        [string]$Input,
        [string]$Output,
        [double]$Duration
    )
    
    Write-Log "[预览] 开始生成预览视频 (WebM格式)..." "Yellow"
    
    # 10段预览，每段1秒，均匀分布（与主服务器保持一致）
    $numSegments = 10
    $segDuration = 1.0
    
    if ($Duration -lt 10) {
        $numSegments = [math]::Max(1, [int]$Duration)
        $segDuration = [math]::Min(1.0, $Duration / $numSegments)
    }
    
    $tempDir = Split-Path $Output -Parent
    $tempFiles = @()
    
    # 生成每个分段
    for ($i = 0; $i -lt $numSegments; $i++) {
        # 均匀分布：从5%到95%
        if ($numSegments -gt 1) {
            $position = 0.05 + (0.9 * $i / ($numSegments - 1))
        } else {
            $position = 0.5
        }
        $startTime = $Duration * $position
        
        # 确保不超过视频末尾
        if ($startTime + $segDuration -gt $Duration) {
            $startTime = [math]::Max(0, $Duration - $segDuration)
        }
        
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
        
        $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
        $roundedTime = [math]::Round($startTime, 1)
        Write-Log "  片段 $($i+1)/$numSegments: ${roundedTime}秒" "Gray"
    }
    
    # 创建拼接列表
    $concatFile = Join-Path $tempDir "concat_list.txt"
    $concatContent = ""
    foreach ($tempPath in $tempFiles) {
        if (Test-Path $tempPath) {
            $safePath = $tempPath.Replace('\', '/')
            $concatContent += "file '$safePath'`n"
        }
    }
    $concatContent | Out-File -FilePath $concatFile -Encoding UTF8 -NoNewline
    
    # 拼接所有片段
    $concatArgs = @(
        "-f", "concat",
        "-safe", "0",
        "-i", $concatFile,
        "-c:v", "libvpx-vp9",
        "-b:v", "500k",
        "-y",
        $Output
    )
    
    Write-Log "  拼接 $numSegments 个片段..." "Gray"
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $concatArgs -NoNewWindow -Wait -PassThru
    
    # 清理临时文件
    foreach ($tempPath in $tempFiles) {
        if (Test-Path $tempPath) { Remove-Item $tempPath -Force }
    }
    if (Test-Path $concatFile) { Remove-Item $concatFile -Force }
    
    if ($process.ExitCode -eq 0 -and (Test-Path $Output)) {
        $fileSize = (Get-Item $Output).Length / 1KB
        $totalDuration = $numSegments * $segDuration
        $roundedDuration = [math]::Round($totalDuration, 1)
        $roundedSize = [math]::Round($fileSize, 1)
        Write-Log "[预览] 完成! $numSegments 段共 ${roundedDuration}秒, 大小: ${roundedSize}KB" "Green"
        return $true
    } else {
        Write-Log "[预览] 失败!" "Red"
        return $false
    }
}

# ========== 主流程 ==========
Write-Log "==========================================" "Cyan"
Write-Log "开始处理视频: $InputFile" "Cyan"
Write-Log "==========================================" "Cyan"

# 检查输入文件
if (-not (Test-Path $InputFile)) {
    Write-Log "错误: 输入文件不存在: $InputFile" "Red"
    exit 1
}

# 创建输出目录
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# 生成文件名
$baseName = if ($VideoId) { $VideoId } else { [System.IO.Path]::GetFileNameWithoutExtension($InputFile) }
$videoOutput = Join-Path $OutputDir "$baseName.mp4"
$coverOutput = Join-Path $OutputDir "$baseName.webp"
$previewOutput = Join-Path $OutputDir "${baseName}_preview.webm"

# 获取视频信息
$duration = Get-VideoDuration -VideoPath $InputFile
$height = Get-VideoHeight -VideoPath $InputFile
Write-Log "视频信息: 时长=${duration}秒, 高度=${height}p" "White"

# 1. 转码视频
$transcodeSuccess = Start-VideoTranscode -Input $InputFile -Output $videoOutput
if (-not $transcodeSuccess) {
    Write-Log "转码失败，终止处理" "Red"
    exit 1
}

# 2. 生成封面（使用转码后的视频）
$coverSuccess = New-VideoCover -Input $videoOutput -Output $coverOutput -Duration $duration

# 3. 生成预览（使用转码后的视频）
$previewSuccess = New-VideoPreview -Input $videoOutput -Output $previewOutput -Duration $duration

# 输出结果
Write-Log "==========================================" "Cyan"
Write-Log "处理完成!" "Green"
Write-Log "  视频: $videoOutput" "White"
Write-Log "  封面: $(if ($coverSuccess) { $coverOutput } else { '生成失败' })" "White"
Write-Log "  预览: $(if ($previewSuccess) { $previewOutput } else { '生成失败' })" "White"
Write-Log "==========================================" "Cyan"

# 返回结果（JSON格式，方便解析）
$result = @{
    success = $transcodeSuccess
    video = $videoOutput
    cover = if ($coverSuccess) { $coverOutput } else { $null }
    preview = if ($previewSuccess) { $previewOutput } else { $null }
    duration = $duration
}

$result | ConvertTo-Json | Write-Output

exit 0
