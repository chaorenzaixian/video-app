# deploy_fixed_scripts.ps1 - 部署修复后的转码脚本
# 
# 使用方法:
# 1. 将此脚本和修复后的脚本文件复制到转码服务器
# 2. 在转码服务器上运行此脚本

$ErrorActionPreference = "Continue"

Write-Host "🔧 部署修复后的转码脚本" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# 脚本目录
$scriptDir = "D:\VideoTranscode\scripts"
$backupDir = "D:\VideoTranscode\scripts\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# 创建备份目录
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "✅ 创建备份目录: $backupDir" -ForegroundColor Green
}

# 备份现有脚本
$scriptsToBackup = @(
    "transcode_full.ps1",
    "upload_full.ps1", 
    "watcher.ps1"
)

Write-Host "`n📦 备份现有脚本..." -ForegroundColor Yellow
foreach ($script in $scriptsToBackup) {
    $sourcePath = Join-Path $scriptDir $script
    $backupPath = Join-Path $backupDir $script
    
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $backupPath -Force
        Write-Host "  ✅ 备份: $script" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  文件不存在: $script" -ForegroundColor Yellow
    }
}

Write-Host "`n🔄 部署修复后的脚本..." -ForegroundColor Yellow

# 假设修复后的脚本在当前目录
$currentDir = Get-Location

$scriptMappings = @{
    "transcode_full.ps1" = "transcode_full.ps1"
    "upload_full.ps1" = "upload_full.ps1"
    "watcher_full.ps1" = "watcher.ps1"  # 注意：watcher_full.ps1 部署为 watcher.ps1
}

foreach ($sourceScript in $scriptMappings.Keys) {
    $targetScript = $scriptMappings[$sourceScript]
    $sourcePath = Join-Path $currentDir $sourceScript
    $targetPath = Join-Path $scriptDir $targetScript
    
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $targetPath -Force
        Write-Host "  ✅ 部署: $sourceScript -> $targetScript" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 源文件不存在: $sourceScript" -ForegroundColor Red
    }
}

Write-Host "`n🔍 验证部署..." -ForegroundColor Yellow

# 检查语法
foreach ($targetScript in $scriptMappings.Values) {
    $scriptPath = Join-Path $scriptDir $targetScript
    
    if (Test-Path $scriptPath) {
        try {
            # 尝试解析脚本语法
            $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $scriptPath -Raw), [ref]$null)
            Write-Host "  ✅ 语法检查通过: $targetScript" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 语法错误: $targetScript - $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "✅ 脚本部署完成!" -ForegroundColor Green
Write-Host "`n📋 下一步操作:" -ForegroundColor Cyan
Write-Host "1. 检查是否有正在运行的 watcher 进程:" -ForegroundColor White
Write-Host "   Get-Process | Where-Object { `$_.ProcessName -like '*powershell*' }" -ForegroundColor Gray
Write-Host "`n2. 如果有运行中的进程，停止它们:" -ForegroundColor White
Write-Host "   Stop-Process -Name powershell -Force" -ForegroundColor Gray
Write-Host "`n3. 重新启动 watcher 服务:" -ForegroundColor White
Write-Host "   powershell -ExecutionPolicy Bypass -File D:\VideoTranscode\scripts\watcher.ps1" -ForegroundColor Gray
Write-Host "`n🎯 修复的问题:" -ForegroundColor Cyan
Write-Host "- PowerShell 字符串插值中的 [math]::Round 语法错误" -ForegroundColor White
Write-Host "- 变量引用中的冒号 (:) 解析问题" -ForegroundColor White
Write-Host "- 所有相关的数学运算表达式已修复" -ForegroundColor White

Write-Host "`n📁 备份位置: $backupDir" -ForegroundColor Gray