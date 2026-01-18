# upload_full.ps1 - 上传转码结果到主服务器（视频+封面+预览）
# 部署到转码服务器: D:\VideoTranscode\scripts\upload_full.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$VideoFile,
    
    [string]$CoverFile = "",
    
    [string]$PreviewFile = "",
    
    [string]$VideoId = "",  # 用于回调通知
    
    [string]$VideoType = "long"  # long 或 short
)

$ErrorActionPreference = "Continue"

# ========== 配置 ==========
$mainServer = "38.47.218.137"
$mainUser = "root"
$keyFile = "C:\server_key"
$transcodeKey = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"

# 根据视频类型选择上传目录
if ($VideoType -eq "short") {
    $videoUploadPath = "/www/wwwroot/video-app/backend/uploads/shorts/"
    $coverUploadPath = "/www/wwwroot/video-app/backend/uploads/shorts/thumbnails/"
    $previewUploadPath = "/www/wwwroot/video-app/backend/uploads/shorts/previews/"
} else {
    $videoUploadPath = "/www/wwwroot/video-app/backend/uploads/videos/"
    $coverUploadPath = "/www/wwwroot/video-app/backend/uploads/thumbnails/"
    $previewUploadPath = "/www/wwwroot/video-app/backend/uploads/previews/"
}

$logFile = "D:\VideoTranscode\logs\upload.log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append
    Write-Host $logMessage -ForegroundColor $Color
}

function Upload-File {
    param(
        [string]$LocalFile,
        [string]$RemotePath
    )
    
    if (-not (Test-Path $LocalFile)) {
        Write-Log "  文件不存在: $LocalFile" "Yellow"
        return $false
    }
    
    $fileName = Split-Path $LocalFile -Leaf
    $fileSize = (Get-Item $LocalFile).Length / 1MB
    $roundedSize = [math]::Round($fileSize, 2)
    
    Write-Log "  上传: $fileName (${roundedSize}MB)" "Gray"
    
    $scpArgs = @(
        "-i", $keyFile,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        $LocalFile,
        "${mainUser}@${mainServer}:${RemotePath}"
    )
    
    try {
        $process = Start-Process -FilePath "scp" -ArgumentList $scpArgs -NoNewWindow -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Log "  成功: $fileName" "Green"
            return $true
        } else {
            Write-Log "  失败: $fileName (退出码: $($process.ExitCode))" "Red"
            return $false
        }
    } catch {
        Write-Log "  异常: $_" "Red"
        return $false
    }
}

function Send-Callback {
    param(
        [string]$VideoId,
        [string]$Status,
        [string]$VideoUrl,
        [string]$CoverUrl,
        [string]$PreviewUrl,
        [double]$Duration = 0,
        [string]$ErrorMessage = ""
    )
    
    Write-Log "[回调] 通知主服务器..." "Yellow"
    
    $body = @{
        video_id = [int]$VideoId
        status = $Status
        thumbnail_url = $CoverUrl
        preview_url = $PreviewUrl
        hls_url = $VideoUrl
        duration = $Duration
        error_message = $ErrorMessage
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod `
            -Uri "http://${mainServer}:8000/api/v1/admin/transcode-callback" `
            -Method POST `
            -Headers @{ "X-Transcode-Key" = $transcodeKey; "Content-Type" = "application/json" } `
            -Body $body `
            -TimeoutSec 30
        
        Write-Log "[回调] 成功: $($response | ConvertTo-Json -Compress)" "Green"
        return $true
    } catch {
        Write-Log "[回调] 失败: $_" "Red"
        return $false
    }
}

# ========== 主流程 ==========
Write-Log "==========================================" "Cyan"
Write-Log "开始上传转码结果" "Cyan"
Write-Log "==========================================" "Cyan"

# 检查SSH密钥
if (-not (Test-Path $keyFile)) {
    Write-Log "错误: SSH密钥不存在: $keyFile" "Red"
    exit 1
}

$startTime = Get-Date
$uploadResults = @{
    video = $false
    cover = $false
    preview = $false
}

# 1. 上传视频
Write-Log "[1/3] 上传视频文件..." "Yellow"
if (Test-Path $VideoFile) {
    $uploadResults.video = Upload-File -LocalFile $VideoFile -RemotePath $videoUploadPath
} else {
    Write-Log "  视频文件不存在: $VideoFile" "Red"
}

# 2. 上传封面
Write-Log "[2/3] 上传封面图片..." "Yellow"
if ($CoverFile -and (Test-Path $CoverFile)) {
    $uploadResults.cover = Upload-File -LocalFile $CoverFile -RemotePath $coverUploadPath
} else {
    Write-Log "  跳过封面上传（文件不存在或未指定）" "Gray"
}

# 3. 上传预览
Write-Log "[3/3] 上传预览视频..." "Yellow"
if ($PreviewFile -and (Test-Path $PreviewFile)) {
    $uploadResults.preview = Upload-File -LocalFile $PreviewFile -RemotePath $previewUploadPath
} else {
    Write-Log "  跳过预览上传（文件不存在或未指定）" "Gray"
}

$endTime = Get-Date
$totalDuration = ($endTime - $startTime).TotalSeconds

# 统计结果
Write-Log "==========================================" "Cyan"
$roundedDuration = [math]::Round($totalDuration, 1)
Write-Log "上传完成! 总耗时: ${roundedDuration}秒" "Green"
Write-Log "  视频: $(if ($uploadResults.video) { '✓' } else { '✗' })" "White"
Write-Log "  封面: $(if ($uploadResults.cover) { '✓' } else { '✗' })" "White"
Write-Log "  预览: $(if ($uploadResults.preview) { '✓' } else { '✗' })" "White"

# 4. 发送回调通知（如果提供了VideoId）
if ($VideoId) {
    $videoFileName = Split-Path $VideoFile -Leaf
    $coverFileName = if ($CoverFile) { Split-Path $CoverFile -Leaf } else { "" }
    $previewFileName = if ($PreviewFile) { Split-Path $PreviewFile -Leaf } else { "" }
    
    $videoUrl = "/uploads/videos/$videoFileName"
    $coverUrl = if ($uploadResults.cover) { "/uploads/thumbnails/$coverFileName" } else { "" }
    $previewUrl = if ($uploadResults.preview) { "/uploads/previews/$previewFileName" } else { "" }
    
    # 获取视频时长
    $duration = 0
    try {
        $ffprobeOutput = & ffprobe -v error -show_entries format=duration -of csv=p=0 $VideoFile 2>$null
        if ($ffprobeOutput) {
            $duration = [double]$ffprobeOutput
        }
    } catch {}
    
    if ($uploadResults.video) {
        Send-Callback -VideoId $VideoId -Status "success" `
            -VideoUrl $videoUrl -CoverUrl $coverUrl -PreviewUrl $previewUrl -Duration $duration
    } else {
        Send-Callback -VideoId $VideoId -Status "failed" `
            -VideoUrl "" -CoverUrl "" -PreviewUrl "" -Duration 0 -ErrorMessage "视频上传失败"
    }
}

Write-Log "==========================================" "Cyan"

# 返回结果
if ($uploadResults.video) {
    exit 0
} else {
    exit 1
}
