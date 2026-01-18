# transcode.ps1 - 视频转码脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputFile
)

$logFile = "C:\VideoTranscode\logs\transcode_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "开始转码: $InputFile" -ForegroundColor Yellow
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 开始转码: $InputFile" | Out-File $logFile

if (-not (Test-Path $InputFile)) {
    Write-Host "错误: 输入文件不存在" -ForegroundColor Red
    exit 1
}

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

try {
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $arguments -NoNewWindow -Wait -PassThru -RedirectStandardError "$logFile.err"
    
    if ($process.ExitCode -eq 0) {
        Write-Host "转码完成: $OutputFile" -ForegroundColor Green
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 转码成功" | Out-File $logFile -Append
        exit 0
    } else {
        Write-Host "转码失败，退出码: $($process.ExitCode)" -ForegroundColor Red
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - 转码失败" | Out-File $logFile -Append
        exit 1
    }
} catch {
    Write-Host "转码异常: $_" -ForegroundColor Red
    exit 1
}
