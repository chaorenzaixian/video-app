@echo off
echo ========================================
echo 远程配置转码服务
echo ========================================
echo.

echo [1/4] 创建转码脚本...
powershell -Command "$script = @'^
# transcode.ps1^
param(^
    [Parameter(Mandatory=$true)]^
    [string]$InputFile,^
    [Parameter(Mandatory=$true)]^
    [string]$OutputFile^
)^
^
$logFile = \"C:\VideoTranscode\logs\transcode_$(Get-Date -Format 'yyyyMMdd_HHmmss').log\"^
Write-Host \"开始转码: $InputFile\" -ForegroundColor Yellow^
\"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 开始转码: $InputFile\" | Out-File $logFile^
^
if (-not (Test-Path $InputFile)) {^
    Write-Host \"错误: 输入文件不存在\" -ForegroundColor Red^
    exit 1^
}^
^
$arguments = @(^
    \"-i\", $InputFile,^
    \"-c:v\", \"libx264\",^
    \"-preset\", \"medium\",^
    \"-crf\", \"23\",^
    \"-c:a\", \"aac\",^
    \"-b:a\", \"128k\",^
    \"-movflags\", \"+faststart\",^
    \"-y\",^
    $OutputFile^
)^
^
try {^
    $process = Start-Process -FilePath \"ffmpeg\" -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardError \"$logFile.err\"^
    if ($process.ExitCode -eq 0) {^
        Write-Host \"转码完成: $OutputFile\" -ForegroundColor Green^
        exit 0^
    } else {^
        Write-Host \"转码失败\" -ForegroundColor Red^
        exit 1^
    }^
} catch {^
    Write-Host \"转码异常: $_\" -ForegroundColor Red^
    exit 1^
}^
'@; $script | Out-File C:\VideoTranscode\scripts\transcode.ps1 -Encoding UTF8"

echo [2/4] 创建监控服务...
powershell -Command "$script = @'^
# watcher.ps1^
$watchFolder = \"C:\VideoTranscode\downloads\"^
$processingFolder = \"C:\VideoTranscode\processing\"^
$completedFolder = \"C:\VideoTranscode\completed\"^
$logFile = \"C:\VideoTranscode\logs\watcher.log\"^
^
function Write-Log {^
    param($Message)^
    $timestamp = Get-Date -Format \"yyyy-MM-dd HH:mm:ss\"^
    \"$timestamp - $Message\" | Out-File -FilePath $logFile -Append^
    Write-Host \"$timestamp - $Message\"^
}^
^
Write-Host \"监控服务启动\" -ForegroundColor Green^
Write-Log \"监控服务启动\"^
^
while ($true) {^
    $videos = Get-ChildItem -Path $watchFolder -Include *.mp4,*.avi,*.mov,*.mkv -ErrorAction SilentlyContinue^
    foreach ($video in $videos) {^
        Write-Log \"发现视频: $($video.Name)\"^
        $processingPath = Join-Path $processingFolder $video.Name^
        Move-Item -Path $video.FullName -Destination $processingPath -Force^
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($video.Name)^
        $outputName = \"${baseName}_transcoded.mp4\"^
        $outputPath = Join-Path $completedFolder $outputName^
        Write-Log \"开始转码...\"^
        ^& \"C:\VideoTranscode\scripts\transcode.ps1\" -InputFile $processingPath -OutputFile $outputPath^
        if ($LASTEXITCODE -eq 0) {^
            Write-Log \"转码成功\"^
            Remove-Item -Path $processingPath -Force^
        }^
    }^
    Start-Sleep -Seconds 10^
}^
'@; $script | Out-File C:\VideoTranscode\scripts\watcher.ps1 -Encoding UTF8"

echo [3/4] 创建启动脚本...
echo Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy Bypass", "-File C:\VideoTranscode\scripts\watcher.ps1" > C:\VideoTranscode\启动监控服务.ps1

echo [4/4] 创建测试脚本...
echo Write-Host "测试FFmpeg..." -ForegroundColor Yellow > C:\VideoTranscode\测试.ps1
echo ffmpeg -version >> C:\VideoTranscode\测试.ps1

echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 文件位置:
echo - 转码脚本: C:\VideoTranscode\scripts\transcode.ps1
echo - 监控服务: C:\VideoTranscode\scripts\watcher.ps1
echo - 启动脚本: C:\VideoTranscode\启动监控服务.ps1
echo.
pause
