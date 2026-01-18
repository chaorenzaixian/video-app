# emergency_fix_transcode.ps1 - 紧急修复转码脚本语法错误
# 直接在转码服务器上运行此脚本来修复问题

$ErrorActionPreference = "Continue"

Write-Host "🚨 紧急修复转码脚本语法错误" -ForegroundColor Red
Write-Host "=" * 50 -ForegroundColor Red

$scriptPath = "D:\VideoTranscode\scripts\transcode_full.ps1"
$backupPath = "D:\VideoTranscode\scripts\transcode_full_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').ps1"

# 检查脚本是否存在
if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 脚本文件不存在: $scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "📦 备份原始脚本..." -ForegroundColor Yellow
Copy-Item -Path $scriptPath -Destination $backupPath -Force
Write-Host "✅ 备份完成: $backupPath" -ForegroundColor Green

Write-Host "🔧 修复语法错误..." -ForegroundColor Yellow

# 读取脚本内容
$content = Get-Content -Path $scriptPath -Raw

# 修复所有的 math::Round 语法错误
$fixes = @(
    @{
        Old = 'Write-Log "  片段 $($i+1)/$numSegments: $([math]::Round($startTime, 1))秒" "Gray"'
        New = '$roundedTime = [math]::Round($startTime, 1)
        Write-Log "  片段 $($i+1)/$numSegments: ${roundedTime}秒" "Gray"'
    },
    @{
        Old = 'Write-Log "[转码] 完成! 耗时: $([math]::Round($duration, 1))秒, 大小: $([math]::Round($fileSize, 2))MB" "Green"'
        New = '$roundedDuration = [math]::Round($duration, 1)
        $roundedSize = [math]::Round($fileSize, 2)
        Write-Log "[转码] 完成! 耗时: ${roundedDuration}秒, 大小: ${roundedSize}MB" "Green"'
    },
    @{
        Old = 'Write-Log "[封面] 完成! 大小: $([math]::Round($fileSize, 1))KB" "Green"'
        New = '$roundedSize = [math]::Round($fileSize, 1)
        Write-Log "[封面] 完成! 大小: ${roundedSize}KB" "Green"'
    },
    @{
        Old = 'Write-Log "[预览] 完成! $numSegments 段共 $([math]::Round($totalDuration, 1))秒, 大小: $([math]::Round($fileSize, 1))KB" "Green"'
        New = '$roundedDuration = [math]::Round($totalDuration, 1)
        $roundedSize = [math]::Round($fileSize, 1)
        Write-Log "[预览] 完成! $numSegments 段共 ${roundedDuration}秒, 大小: ${roundedSize}KB" "Green"'
    }
)

$fixCount = 0
foreach ($fix in $fixes) {
    if ($content -match [regex]::Escape($fix.Old)) {
        $content = $content -replace [regex]::Escape($fix.Old), $fix.New
        $fixCount++
        Write-Host "  ✅ 修复: math::Round 语法错误 #$fixCount" -ForegroundColor Green
    }
}

# 保存修复后的脚本
$content | Set-Content -Path $scriptPath -Encoding UTF8

Write-Host "🔍 验证修复..." -ForegroundColor Yellow

# 语法检查
try {
    $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$null)
    Write-Host "✅ 语法检查通过!" -ForegroundColor Green
} catch {
    Write-Host "❌ 语法检查失败: $_" -ForegroundColor Red
    # 恢复备份
    Copy-Item -Path $backupPath -Destination $scriptPath -Force
    Write-Host "🔄 已恢复备份文件" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n" + "=" * 50 -ForegroundColor Green
Write-Host "✅ 修复完成! 共修复 $fixCount 处错误" -ForegroundColor Green

Write-Host "`n📋 下一步操作:" -ForegroundColor Cyan
Write-Host "1. 停止当前的 watcher 进程:" -ForegroundColor White
Write-Host "   Get-Process | Where-Object { `$_.ProcessName -like '*powershell*' } | Stop-Process -Force" -ForegroundColor Gray

Write-Host "`n2. 重新启动 watcher 服务:" -ForegroundColor White
Write-Host "   powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\watcher.ps1" -ForegroundColor Gray

Write-Host "`n📁 备份文件: $backupPath" -ForegroundColor Gray
Write-Host "🎯 现在应该可以正常处理视频了!" -ForegroundColor Green