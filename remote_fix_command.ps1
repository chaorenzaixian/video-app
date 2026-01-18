# 在转码服务器上执行的完整修复命令
# 复制这些命令到转码服务器的 PowerShell 中逐行执行

Write-Host "🔧 开始修复转码脚本语法错误..." -ForegroundColor Cyan

# 1. 停止 watcher 进程
Write-Host "1. 停止 watcher 进程..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -eq "powershell" } | ForEach-Object {
    if ($_.CommandLine -like "*watcher*" -or $_.Id -ne $PID) {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# 2. 备份原始文件
Write-Host "2. 备份原始文件..." -ForegroundColor Yellow
$scriptPath = "D:\VideoTranscode\scripts\transcode_full.ps1"
$backupPath = "D:\VideoTranscode\scripts\transcode_full_backup_$(Get-Date -Format 'HHmmss').ps1"
Copy-Item $scriptPath $backupPath -Force
Write-Host "   备份到: $backupPath" -ForegroundColor Gray

# 3. 修复语法错误
Write-Host "3. 修复语法错误..." -ForegroundColor Yellow
$content = Get-Content $scriptPath -Raw

# 修复第 219 行的错误
$oldPattern = 'Write-Log "  片段 \$\(\$i\+1\)/\$numSegments: \$\(\[math\]::Round\(\$startTime, 1\)\)秒" "Gray"'
$newCode = '        $roundedTime = [math]::Round($startTime, 1)
        Write-Log "  片段 $($i+1)/$numSegments: ${roundedTime}秒" "Gray"'

if ($content -match [regex]::Escape($oldPattern)) {
    $content = $content -replace [regex]::Escape($oldPattern), $newCode
    Write-Host "   ✅ 修复了第 219 行的语法错误" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  未找到第 219 行的错误模式，尝试其他修复..." -ForegroundColor Yellow
    # 通用修复：替换所有的 math::Round 表达式
    $content = $content -replace '\$\(\[math\]::Round\(\$([^,]+),\s*([^)]+)\)\)', '${$1Rounded}'
    $content = $content -replace '(\$\{[^}]+Rounded\})', { 
        param($match)
        $varName = $match.Groups[1].Value -replace '\$\{([^R]+)Rounded\}', '$1'
        "`$rounded = [math]::Round(`$$varName, 1); `${rounded}"
    }
}

# 保存修复后的文件
$content | Set-Content $scriptPath -Encoding UTF8

# 4. 验证语法
Write-Host "4. 验证语法..." -ForegroundColor Yellow
try {
    $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$null)
    Write-Host "   ✅ 语法检查通过!" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 语法检查失败: $_" -ForegroundColor Red
    Copy-Item $backupPath $scriptPath -Force
    Write-Host "   已恢复备份文件" -ForegroundColor Yellow
    exit 1
}

# 5. 重启 watcher 服务
Write-Host "5. 重启 watcher 服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "D:\VideoTranscode\scripts\watcher.ps1" -WindowStyle Minimized

Write-Host "`n✅ 修复完成!" -ForegroundColor Green
Write-Host "📁 备份文件: $backupPath" -ForegroundColor Gray
Write-Host "🎯 watcher 服务已重启，现在应该可以正常处理视频了!" -ForegroundColor Green