# Windows 转码服务器完整配置脚本
# 请在服务器上以管理员身份运行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频转码服务器完整配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$workDir = "C:\VideoTranscode"

# 1. 创建目录结构
Write-Host "[1/6] 创建目录结构..." -ForegroundColor Yellow
$dirs = @("downloads", "processing", "completed", "logs", "scripts")
foreach ($dir in $dirs) {
    $path = Join-Path $workDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  创建: $path" -ForegroundColor Gray
    } else {
        Write-Host "  已存在: $path" -ForegroundColor Gray
    }
}
Write-Host "✓ 目录创建完成" -ForegroundColor Green
Write-Host ""

# 2. 创建转码脚本
Write-Host "[2/6] 创建转码脚本..." -ForegroundColor Yellow

$transcodeScript = @'
# transcode.ps1 - 视频转码脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputFile
)

$logFile = "C:\VideoTranscode\logs\transcode_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "开始转码" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "输入: $InputFile" -ForegroundColor White
Write-Host "输出: $OutputFile" -ForegroundColor White
Write-Host ""

"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 开始转码" | Out-File $logFile
"输入文件: $InputFile" | Out-File $logFile -Append
"输出文件: $OutputFile" | Out-File $logFile -Append

# 检查输入文件
if (-not (Test-Path $InputFile)) {
    Write-Host "错误: 输入文件不存在" -ForegroundColor Red
    "错误: 输入文件不存在" | Out-File $logFile -Append
    exit 1
}

$inputSize = (Get-Item $InputFile).Length / 1MB
Write-Host "文件大小: $([math]::Round($inputSize, 2)) MB" -ForegroundColor Gray
"文件大小: $inputSize MB" | Out-File $logFile -Append

# FFmpeg 参数
$arguments = @(
    "-i", $InputFile,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    "-y",
    $OutputFile
)

Write-Host "开始转码..." -ForegroundColor Yellow
$startTime = Get-Date

try {
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardError "$logFile.err"
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($process.ExitCode -eq 0) {
        $outputSize = (Get-Item $OutputFile).Length / 1MB
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "转码成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "输出大小: $([math]::Round($outputSize, 2)) MB" -ForegroundColor White
        Write-Host "耗时: $([math]::Round($duration, 2)) 秒" -ForegroundColor White
        Write-Host "压缩率: $([math]::Round(($inputSize - $outputSize) / $inputSize * 100, 2))%" -ForegroundColor White
        Write-Host ""
        
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 转码成功" | Out-File $logFile -Append
        "输出大小: $outputSize MB" | Out-File $logFile -Append
        "耗时: $duration 秒" | Out-File $logFile -Append
        
        exit 0
    } else {
        Write-Host ""
        Write-Host "转码失败，退出码: $($process.ExitCode)" -ForegroundColor Red
        Write-Host "查看错误日志: $logFile.err" -ForegroundColor Yellow
        
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 转码失败，退出码: $($process.ExitCode)" | Out-File $logFile -Append
        
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "转码异常: $_" -ForegroundColor Red
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 转码异常: $_" | Out-File $logFile -Append
    exit 1
}
'@

$transcodeScript | Out-File -FilePath "$workDir\scripts\transcode.ps1" -Encoding UTF8
Write-Host "✓ 转码脚本已创建: $workDir\scripts\transcode.ps1" -ForegroundColor Green
Write-Host ""

# 3. 创建监控服务脚本
Write-Host "[3/6] 创建监控服务..." -ForegroundColor Yellow

$watcherScript = @'
# watcher.ps1 - 视频转码监控服务
$watchFolder = "C:\VideoTranscode\downloads"
$processingFolder = "C:\VideoTranscode\processing"
$completedFolder = "C:\VideoTranscode\completed"
$logFile = "C:\VideoTranscode\logs\watcher.log"
$mainServerIP = "38.47.218.137"
$uploadPath = "/www/wwwroot/video-app/backend/uploads/videos"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    $logMessage | Out-File -FilePath $logFile -Append
    Write-Host $logMessage -ForegroundColor $Color
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频转码监控服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "监控目录: $watchFolder" -ForegroundColor White
Write-Host "处理目录: $processingFolder" -ForegroundColor White
Write-Host "完成目录: $completedFolder" -ForegroundColor White
Write-Host "日志文件: $logFile" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

Write-Log "监控服务启动" "Green"

$processedCount = 0
$failedCount = 0

while ($true) {
    try {
        # 查找待处理的视频文件
        $videos = Get-ChildItem -Path $watchFolder -Include *.mp4,*.avi,*.mov,*.mkv,*.flv -ErrorAction SilentlyContinue
        
        if ($videos.Count -gt 0) {
            Write-Log "发现 $($videos.Count) 个待处理视频" "Yellow"
        }
        
        foreach ($video in $videos) {
            Write-Log "========================================" "Cyan"
            Write-Log "处理视频: $($video.Name)" "Cyan"
            
            # 移动到处理目录
            $processingPath = Join-Path $processingFolder $video.Name
            try {
                Move-Item -Path $video.FullName -Destination $processingPath -Force
                Write-Log "已移动到处理目录" "Gray"
            } catch {
                Write-Log "移动文件失败: $_" "Red"
                continue
            }
            
            # 生成输出文件名
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name)
            $outputName = "${baseName}_transcoded.mp4"
            $outputPath = Join-Path $completedFolder $outputName
            
            # 转码
            Write-Log "开始转码..." "Yellow"
            $transcodeStart = Get-Date
            
            $result = & "C:\VideoTranscode\scripts\transcode.ps1" -InputFile $processingPath -OutputFile $outputPath
            
            $transcodeEnd = Get-Date
            $transcodeDuration = ($transcodeEnd - $transcodeStart).TotalSeconds
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "转码成功，耗时: $([math]::Round($transcodeDuration, 2)) 秒" "Green"
                $processedCount++
                
                # 删除原文件
                Remove-Item -Path $processingPath -Force
                Write-Log "已删除原文件" "Gray"
                
                # 上传到主服务器（可选）
                Write-Log "准备上传到主服务器..." "Yellow"
                # TODO: 实现上传逻辑
                
                Write-Log "视频处理完成: $outputName" "Green"
                Write-Log "总计处理: $processedCount 个，失败: $failedCount 个" "White"
            } else {
                Write-Log "转码失败" "Red"
                $failedCount++
                
                # 将失败的文件移回下载目录
                Move-Item -Path $processingPath -Destination $video.FullName -Force -ErrorAction SilentlyContinue
            }
            
            Write-Log "========================================" "Cyan"
            Write-Host ""
        }
        
        # 等待10秒后继续检查
        Start-Sleep -Seconds 10
        
    } catch {
        Write-Log "监控服务异常: $_" "Red"
        Start-Sleep -Seconds 30
    }
}
'@

$watcherScript | Out-File -FilePath "$workDir\scripts\watcher.ps1" -Encoding UTF8
Write-Host "✓ 监控服务已创建: $workDir\scripts\watcher.ps1" -ForegroundColor Green
Write-Host ""

# 4. 创建启动脚本
Write-Host "[4/6] 创建启动脚本..." -ForegroundColor Yellow

$startScript = @'
# 启动转码监控服务
Write-Host "正在启动转码监控服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File C:\VideoTranscode\scripts\watcher.ps1"
Write-Host "转码监控服务已启动！" -ForegroundColor Green
Write-Host "服务运行在新窗口中" -ForegroundColor White
'@

$startScript | Out-File -FilePath "$workDir\启动监控服务.ps1" -Encoding UTF8
Write-Host "✓ 启动脚本已创建: $workDir\启动监控服务.ps1" -ForegroundColor Green
Write-Host ""

# 5. 创建测试脚本
Write-Host "[5/6] 创建测试脚本..." -ForegroundColor Yellow

$testScript = @'
# 测试转码功能
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "转码功能测试" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 FFmpeg
Write-Host "检查 FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✓ FFmpeg 已安装: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ FFmpeg 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host "请先安装 FFmpeg" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 创建测试视频
Write-Host "创建测试视频..." -ForegroundColor Yellow
$testInput = "C:\VideoTranscode\downloads\test_input.mp4"
$testOutput = "C:\VideoTranscode\completed\test_output.mp4"

# 使用 FFmpeg 创建一个5秒的测试视频
& ffmpeg -f lavfi -i testsrc=duration=5:size=1280x720:rate=30 -pix_fmt yuv420p -y $testInput 2>$null

if (Test-Path $testInput) {
    Write-Host "✓ 测试视频已创建: $testInput" -ForegroundColor Green
    $inputSize = (Get-Item $testInput).Length / 1MB
    Write-Host "  大小: $([math]::Round($inputSize, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "✗ 测试视频创建失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 测试转码
Write-Host "测试转码..." -ForegroundColor Yellow
& "C:\VideoTranscode\scripts\transcode.ps1" -InputFile $testInput -OutputFile $testOutput

if ($LASTEXITCODE -eq 0 -and (Test-Path $testOutput)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 转码测试成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    $outputSize = (Get-Item $testOutput).Length / 1MB
    Write-Host "输出文件: $testOutput" -ForegroundColor White
    Write-Host "输出大小: $([math]::Round($outputSize, 2)) MB" -ForegroundColor White
    
    # 清理测试文件
    Write-Host ""
    Write-Host "清理测试文件..." -ForegroundColor Gray
    Remove-Item $testInput -Force -ErrorAction SilentlyContinue
    Remove-Item $testOutput -Force -ErrorAction SilentlyContinue
    Write-Host "✓ 清理完成" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ 转码测试失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "所有测试通过！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以:" -ForegroundColor Cyan
Write-Host "1. 将视频文件放入 C:\VideoTranscode\downloads" -ForegroundColor White
Write-Host "2. 运行 C:\VideoTranscode\启动监控服务.ps1 启动自动转码" -ForegroundColor White
Write-Host ""
'@

$testScript | Out-File -FilePath "$workDir\测试转码.ps1" -Encoding UTF8
Write-Host "✓ 测试脚本已创建: $workDir\测试转码.ps1" -ForegroundColor Green
Write-Host ""

# 6. 创建桌面快捷方式
Write-Host "[6/6] 创建桌面快捷方式..." -ForegroundColor Yellow

try {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    
    # 启动服务快捷方式
    $shortcut1Path = Join-Path $desktopPath "启动转码服务.lnk"
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut1 = $WScriptShell.CreateShortcut($shortcut1Path)
    $shortcut1.TargetPath = "powershell.exe"
    $shortcut1.Arguments = "-ExecutionPolicy Bypass -File `"$workDir\启动监控服务.ps1`""
    $shortcut1.WorkingDirectory = $workDir
    $shortcut1.IconLocation = "shell32.dll,137"
    $shortcut1.Description = "启动视频转码监控服务"
    $shortcut1.Save()
    Write-Host "  ✓ 创建: 启动转码服务.lnk" -ForegroundColor Gray
    
    # 测试转码快捷方式
    $shortcut2Path = Join-Path $desktopPath "测试转码功能.lnk"
    $shortcut2 = $WScriptShell.CreateShortcut($shortcut2Path)
    $shortcut2.TargetPath = "powershell.exe"
    $shortcut2.Arguments = "-ExecutionPolicy Bypass -File `"$workDir\测试转码.ps1`""
    $shortcut2.WorkingDirectory = $workDir
    $shortcut2.IconLocation = "shell32.dll,165"
    $shortcut2.Description = "测试转码功能"
    $shortcut2.Save()
    Write-Host "  ✓ 创建: 测试转码功能.lnk" -ForegroundColor Gray
    
    # 打开工作目录快捷方式
    $shortcut3Path = Join-Path $desktopPath "转码工作目录.lnk"
    $shortcut3 = $WScriptShell.CreateShortcut($shortcut3Path)
    $shortcut3.TargetPath = $workDir
    $shortcut3.IconLocation = "shell32.dll,4"
    $shortcut3.Description = "打开转码工作目录"
    $shortcut3.Save()
    Write-Host "  ✓ 创建: 转码工作目录.lnk" -ForegroundColor Gray
    
    Write-Host "✓ 桌面快捷方式已创建" -ForegroundColor Green
} catch {
    Write-Host "⚠ 快捷方式创建失败: $_" -ForegroundColor Yellow
}
Write-Host ""

# 完成
Write-Host "========================================" -ForegroundColor Green
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "工作目录: $workDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 双击桌面的 '测试转码功能' 测试转码" -ForegroundColor White
Write-Host "2. 测试通过后，双击 '启动转码服务' 启动监控" -ForegroundColor White
Write-Host "3. 将视频文件放入 $workDir\downloads 自动转码" -ForegroundColor White
Write-Host "4. 转码完成的文件在 $workDir\completed" -ForegroundColor White
Write-Host ""
Write-Host "日志文件: $workDir\logs" -ForegroundColor Gray
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
