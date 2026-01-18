# fix_line_219.ps1 - 专门修复第 219 行的语法错误
# 在转码服务器上运行

Write-Host "🔧 修复 transcode_full.ps1 第 219 行语法错误" -ForegroundColor Cyan

$scriptPath = "D:\VideoTranscode\scripts\transcode_full.ps1"

# 停止 watcher 进程
Write-Host "1. 停止 watcher 进程..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -like "*powershell*" -and $_.CommandLine -like "*watcher*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 备份
Write-Host "2. 备份原始文件..." -ForegroundColor Yellow
$backupPath = "D:\VideoTranscode\scripts\transcode_full_backup_$(Get-Date -Format 'HHmmss').ps1"
Copy-Item $scriptPath $backupPath -Force

# 读取并修复
Write-Host "3. 修复语法错误..." -ForegroundColor Yellow
$lines = Get-Content $scriptPath

for ($i = 0; $i -lt $lines.Count; $i++) {
    # 修复第 219 行附近的 math::Round 错误
    if ($lines[$i] -match 'Write-Log.*\$\(\[math\]::Round\(\$startTime.*\).*秒.*Gray') {
        Write-Host "   找到错误行 $($i+1): $($lines[$i])" -ForegroundColor Red
        $lines[$i] = '        $roundedTime = [math]::Round($startTime, 1)'
        $lines = $lines[0..$i] + '        Write-Log "  片段 $($i+1)/$numSegments: ${roundedTime}秒" "Gray"' + $lines[($i+1)..($lines.Count-1)]
        Write-Host "   已修复!" -ForegroundColor Green
        break
    }
}

# 保存修复后的文件
$lines | Set-Content $scriptPath -Encoding UTF8

Write-Host "4. 验证语法..." -ForegroundColor Yellow
try {
    $testContent = Get-Content $scriptPath -Raw
    $null = [System.Management.Automation.PSParser]::Tokenize($testContent, [ref]$null)
    Write-Host "   ✅ 语法检查通过!" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 语法检查失败: $_" -ForegroundColor Red
    Copy-Item $backupPath $scriptPath -Force
    Write-Host "   已恢复备份" -ForegroundColor Yellow
    exit 1
}

Write-Host "5. 重启 watcher 服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "D:\VideoTranscode\scripts\watcher.ps1" -WindowStyle Hidden

Write-Host "`n✅ 修复完成! 备份文件: $backupPath" -ForegroundColor Green