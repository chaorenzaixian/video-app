# watcher_full.ps1 - 完整视频处理监控服务
# 部署到转码服务器: D:\VideoTranscode\scripts\watcher.ps1
# 
# 功能: 监控下载目录，自动完成 转码→生成封面→生成预览→上传→清理
# 支持长视频和短视频分开处理

$ErrorActionPreference = "Continue"

# ========== 配置 ==========
$config = @{
    # 长视频目录
    LongVideoDir = "D:\VideoTranscode\downloads\long"
    # 短视频目录
    ShortVideoDir = "D:\VideoTranscode\downloads\short"
    
    ProcessingDir = "D:\VideoTranscode\processing"
    CompletedDir = "D:\VideoTranscode\completed"
    LogDir = "D:\VideoTranscode\logs"
    
    # 脚本路径
    TranscodeScript = "D:\VideoTranscode\scripts\transcode_full.ps1"
    UploadScript = "D:\VideoTranscode\scripts\upload_full.ps1"
    
    # 主服务器配置
    MainServer = "38.47.218.137"
    TranscodeKey = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"
    
    # 处理选项
    DeleteAfterUpload = $true  # 上传成功后删除本地文件
    CheckInterval = 10         # 检查间隔（秒）
}

$logFile = Join-Path $config.LogDir "watcher_$(Get-Date -Format 'yyyyMMdd').log"

# 确保目录存在
foreach ($dir in @($config.LongVideoDir, $config.ShortVideoDir, $config.ProcessingDir, $config.CompletedDir, $config.LogDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# ========== 函数 ==========
function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append
    Write-Host $logMessage -ForegroundColor $Color
}

function Get-VideoId {
    param([string]$FileName)
    # 从文件名提取视频ID（如果有的话）
    # 格式: video_123.mp4 或 123_xxx.mp4
    if ($FileName -match "^(\d+)") {
        return $matches[1]
    }
    return ""
}

function Process-SingleVideo {
    param(
        [System.IO.FileInfo]$VideoFile,
        [string]$VideoType = "long"  # long 或 short
    )
    
    $baseName = $VideoFile.BaseName
    $videoId = Get-VideoId -FileName $baseName
    
    Write-Log "==========================================" "Cyan"
    Write-Log "开始处理 [$VideoType]: $($VideoFile.Name)" "Cyan"
    if ($videoId) { Write-Log "视频ID: $videoId" "Gray" }
    Write-Log "==========================================" "Cyan"
    
    $processingPath = Join-Path $config.ProcessingDir $VideoFile.Name
    $outputDir = Join-Path $config.CompletedDir $baseName
    
    try {
        # 1. 移动到处理目录
        Write-Log "[1/4] 移动到处理目录..." "Yellow"
        Move-Item -Path $VideoFile.FullName -Destination $processingPath -Force
        Write-Log "  完成" "Green"
        
        # 2. 执行完整转码（转码+封面+预览）
        Write-Log "[2/4] 开始转码处理..." "Yellow"
        $transcodeStart = Get-Date
        
        $transcodeArgs = @(
            "-ExecutionPolicy", "Bypass",
            "-File", $config.TranscodeScript,
            "-InputFile", $processingPath,
            "-OutputDir", $outputDir
        )
        if ($videoId) {
            $transcodeArgs += @("-VideoId", $videoId)
        }
        
        $transcodeProcess = Start-Process -FilePath "powershell" -ArgumentList $transcodeArgs `
            -NoNewWindow -Wait -PassThru
        
        $transcodeEnd = Get-Date
        $transcodeDuration = ($transcodeEnd - $transcodeStart).TotalSeconds
        
        if ($transcodeProcess.ExitCode -ne 0) {
            Write-Log "  转码失败! 退出码: $($transcodeProcess.ExitCode)" "Red"
            # 移回原目录
            Move-Item -Path $processingPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
            return $false
        }
        
        $roundedDuration = [math]::Round($transcodeDuration, 1)
        Write-Log "  转码完成! 耗时: ${roundedDuration}秒" "Green"
        
        # 查找生成的文件
        $videoOutput = Get-ChildItem -Path $outputDir -Filter "*.mp4" | Where-Object { $_.Name -notlike "*_preview*" } | Select-Object -First 1
        $coverOutput = Get-ChildItem -Path $outputDir -Filter "*.webp" -ErrorAction SilentlyContinue | Select-Object -First 1
        $previewOutput = Get-ChildItem -Path $outputDir -Filter "*_preview.webm" -ErrorAction SilentlyContinue | Select-Object -First 1
        
        if (-not $videoOutput) {
            Write-Log "  错误: 找不到转码后的视频文件" "Red"
            return $false
        }
        
        # 3. 上传到主服务器
        Write-Log "[3/4] 上传到主服务器..." "Yellow"
        $uploadStart = Get-Date
        
        $uploadArgs = @(
            "-ExecutionPolicy", "Bypass",
            "-File", $config.UploadScript,
            "-VideoFile", $videoOutput.FullName
        )
        
        if ($coverOutput) {
            $uploadArgs += @("-CoverFile", $coverOutput.FullName)
        }
        if ($previewOutput) {
            $uploadArgs += @("-PreviewFile", $previewOutput.FullName)
        }
        if ($videoId) {
            $uploadArgs += @("-VideoId", $videoId)
        }
        # 传递视频类型
        $uploadArgs += @("-VideoType", $VideoType)
        
        $uploadProcess = Start-Process -FilePath "powershell" -ArgumentList $uploadArgs `
            -NoNewWindow -Wait -PassThru
        
        $uploadEnd = Get-Date
        $uploadDuration = ($uploadEnd - $uploadStart).TotalSeconds
        
        if ($uploadProcess.ExitCode -ne 0) {
            Write-Log "  上传失败! 文件保留在: $outputDir" "Red"
            return $false
        }
        
        $roundedDuration = [math]::Round($uploadDuration, 1)
        Write-Log "  上传完成! 耗时: ${roundedDuration}秒" "Green"
        
        # 4. 清理本地文件
        Write-Log "[4/4] 清理本地文件..." "Yellow"
        
        # 删除原始文件
        if (Test-Path $processingPath) {
            Remove-Item -Path $processingPath -Force
            Write-Log "  删除原始文件" "Gray"
        }
        
        # 删除转码结果（如果配置了）
        if ($config.DeleteAfterUpload) {
            Remove-Item -Path $outputDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "  删除转码结果目录" "Gray"
        }
        
        Write-Log "  清理完成" "Green"
        
        # 总结
        $totalDuration = $transcodeDuration + $uploadDuration
        Write-Log "==========================================" "Cyan"
        Write-Log "处理完成: $($VideoFile.Name)" "Green"
        $roundedTranscode = [math]::Round($transcodeDuration, 1)
        $roundedUpload = [math]::Round($uploadDuration, 1)
        $roundedTotal = [math]::Round($totalDuration, 1)
        Write-Log "  转码耗时: ${roundedTranscode}秒" "White"
        Write-Log "  上传耗时: ${roundedUpload}秒" "White"
        Write-Log "  总耗时: ${roundedTotal}秒" "White"
        Write-Log "==========================================" "Cyan"
        
        return $true
        
    } catch {
        Write-Log "处理异常: $_" "Red"
        # 尝试恢复原始文件
        if (Test-Path $processingPath) {
            Move-Item -Path $processingPath -Destination $VideoFile.FullName -Force -ErrorAction SilentlyContinue
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
Write-Host "长视频目录: $($config.LongVideoDir)" -ForegroundColor White
Write-Host "短视频目录: $($config.ShortVideoDir)" -ForegroundColor White
Write-Host "处理目录: $($config.ProcessingDir)" -ForegroundColor White
Write-Host "完成目录: $($config.CompletedDir)" -ForegroundColor White
Write-Host "日志文件: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "处理流程: 转码 → 生成封面 → 生成预览 → 上传 → 清理" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

Write-Log "监控服务启动" "Green"

$stats = @{
    Processed = 0
    Failed = 0
    StartTime = Get-Date
}

while ($true) {
    try {
        # 查找长视频
        $longVideos = Get-ChildItem -Path $config.LongVideoDir -Filter "*.mp4" -ErrorAction SilentlyContinue
        # 查找短视频
        $shortVideos = Get-ChildItem -Path $config.ShortVideoDir -Filter "*.mp4" -ErrorAction SilentlyContinue
        
        $totalCount = ($longVideos.Count) + ($shortVideos.Count)
        
        if ($totalCount -gt 0) {
            Write-Log "发现 $($longVideos.Count) 个长视频, $($shortVideos.Count) 个短视频" "Yellow"
            
            # 处理长视频
            foreach ($video in $longVideos) {
                # 检查文件是否还在写入（等待文件稳定）
                $initialSize = $video.Length
                Start-Sleep -Seconds 2
                $video.Refresh()
                
                if ($video.Length -ne $initialSize) {
                    Write-Log "文件正在写入，跳过: $($video.Name)" "Gray"
                    continue
                }
                
                # 处理长视频
                $success = Process-SingleVideo -VideoFile $video -VideoType "long"
                
                if ($success) {
                    $stats.Processed++
                } else {
                    $stats.Failed++
                }
                
                # 显示统计
                $runTime = ((Get-Date) - $stats.StartTime).TotalHours
                $roundedTime = [math]::Round($runTime, 1)
                Write-Log "统计: 成功=$($stats.Processed), 失败=$($stats.Failed), 运行时间=${roundedTime}小时" "Gray"
            }
            
            # 处理短视频
            foreach ($video in $shortVideos) {
                # 检查文件是否还在写入（等待文件稳定）
                $initialSize = $video.Length
                Start-Sleep -Seconds 2
                $video.Refresh()
                
                if ($video.Length -ne $initialSize) {
                    Write-Log "文件正在写入，跳过: $($video.Name)" "Gray"
                    continue
                }
                
                # 处理短视频
                $success = Process-SingleVideo -VideoFile $video -VideoType "short"
                
                if ($success) {
                    $stats.Processed++
                } else {
                    $stats.Failed++
                }
                
                # 显示统计
                $runTime = ((Get-Date) - $stats.StartTime).TotalHours
                $roundedTime = [math]::Round($runTime, 1)
                Write-Log "统计: 成功=$($stats.Processed), 失败=$($stats.Failed), 运行时间=${roundedTime}小时" "Gray"
            }
        }
        
        # 等待下一次检查
        Start-Sleep -Seconds $config.CheckInterval
        
    } catch {
        Write-Log "监控循环异常: $_" "Red"
        Start-Sleep -Seconds 30
    }
}
