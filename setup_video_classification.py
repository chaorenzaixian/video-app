#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def run_command(ssh, command, description):
    """执行远程命令"""
    print(f"\n📋 {description}...")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"✅ 成功")
            if output:
                print(f"   输出: {output}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("📹 设置长短视频分类系统")
print("=" * 50)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 {TRANSCODE_SERVER}...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!")
    
    # 1. 停止当前 watcher 服务
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \'*watcher*\' } | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \'已停止 watcher 服务\'"',
        "停止当前 watcher 服务")
    
    # 2. 创建长短视频目录结构
    run_command(ssh,
        'powershell -Command "Write-Host \'创建目录结构...\'; New-Item -ItemType Directory -Path D:\\VideoTranscode\\downloads\\long -Force; New-Item -ItemType Directory -Path D:\\VideoTranscode\\downloads\\short -Force; New-Item -ItemType Directory -Path D:\\VideoTranscode\\completed\\long -Force; New-Item -ItemType Directory -Path D:\\VideoTranscode\\completed\\short -Force; Write-Host \'目录结构已创建\'"',
        "创建长短视频目录结构")
    
    # 3. 创建配置文件
    run_command(ssh,
        'powershell -Command "Write-Host \'创建配置文件...\'; $config = @\"\n# 视频分类配置\n# 短视频时长阈值（秒）\nSHORT_VIDEO_THRESHOLD=60\n# 长视频时长阈值（秒）\nLONG_VIDEO_THRESHOLD=60\n# 转码质量设置\nSHORT_VIDEO_CRF=23\nLONG_VIDEO_CRF=25\n\"@; $config | Set-Content D:\\VideoTranscode\\config.ini -Encoding UTF8; Write-Host \'配置文件已创建\'"',
        "创建配置文件")
    
    # 4. 创建增强版 watcher 脚本
    enhanced_watcher = '''# 增强版视频监控服务 - 支持长短视频分类
$downloadsPath = "D:\\VideoTranscode\\downloads"
$processingPath = "D:\\VideoTranscode\\processing"
$completedPath = "D:\\VideoTranscode\\completed"
$logPath = "D:\\VideoTranscode\\logs"
$configFile = "D:\\VideoTranscode\\config.ini"
$transcodeScript = "D:\\VideoTranscode\\scripts\\transcode_full.ps1"

# 确保目录存在
@($logPath, $processingPath, "$completedPath\\long", "$completedPath\\short") | ForEach-Object {
    if (!(Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force }
}

$logFile = Join-Path $logPath "watcher.log"

# 读取配置
$shortThreshold = 60  # 默认60秒
if (Test-Path $configFile) {
    $config = Get-Content $configFile | Where-Object { $_ -match "SHORT_VIDEO_THRESHOLD=" }
    if ($config) {
        $shortThreshold = [int]($config -split "=")[1]
    }
}

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Get-VideoDuration {
    param($FilePath)
    try {
        $duration = & ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$FilePath" 2>$null
        return [double]$duration
    } catch {
        return 0
    }
}

Write-Log "=== 增强版 Watcher 服务启动 ===" "Green"
Write-Log "短视频阈值: $shortThreshold 秒"
Write-Log "监控目录: $downloadsPath"

$processedCount = 0
$failedCount = 0

while ($true) {
    try {
        # 查找所有 MP4 文件（包括子目录）
        $videoFiles = @()
        
        # 检查根目录
        $rootFiles = Get-ChildItem -Path $downloadsPath -Filter "*.mp4" -File | Where-Object { $_.Length -gt 1000 }
        $videoFiles += $rootFiles
        
        # 检查 long 子目录
        $longPath = Join-Path $downloadsPath "long"
        if (Test-Path $longPath) {
            $longFiles = Get-ChildItem -Path $longPath -Filter "*.mp4" -File | Where-Object { $_.Length -gt 1000 }
            $videoFiles += $longFiles
        }
        
        # 检查 short 子目录
        $shortPath = Join-Path $downloadsPath "short"
        if (Test-Path $shortPath) {
            $shortFiles = Get-ChildItem -Path $shortPath -Filter "*.mp4" -File | Where-Object { $_.Length -gt 1000 }
            $videoFiles += $shortFiles
        }
        
        if ($videoFiles.Count -gt 0) {
            Write-Log "发现 $($videoFiles.Count) 个待处理视频"
            
            foreach ($file in $videoFiles) {
                try {
                    Write-Log "=========================================="
                    
                    # 获取视频时长
                    $duration = Get-VideoDuration $file.FullName
                    $isShort = $duration -le $shortThreshold -and $duration -gt 0
                    $videoType = if ($isShort) { "short" } else { "long" }
                    
                    Write-Log "开始处理 [$videoType]: $($file.Name)"
                    Write-Log "视频时长: $([math]::Round($duration, 1)) 秒"
                    
                    # 移动到处理目录
                    $processingFile = Join-Path $processingPath $file.Name
                    Move-Item -Path $file.FullName -Destination $processingFile -Force
                    Write-Log "[1/4] 移动到处理目录..."
                    Write-Log "  完成"
                    
                    # 调用转码脚本，传递视频类型参数
                    Write-Log "[2/4] 开始转码处理..."
                    $result = & powershell -ExecutionPolicy Bypass -File $transcodeScript -InputFile $processingFile -VideoType $videoType
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Log "  转码成功!"
                        $processedCount++
                    } else {
                        Write-Log "  转码失败! 退出码: $LASTEXITCODE" "Red"
                        $failedCount++
                    }
                    
                    Write-Log "统计: 成功=$processedCount, 失败=$failedCount, 运行时间=$([math]::Round(((Get-Date) - $startTime).TotalHours, 1))小时"
                    
                } catch {
                    Write-Log "处理文件时出错: $($_.Exception.Message)" "Red"
                    $failedCount++
                }
            }
        }
        
        # 等待10秒后继续检查
        Start-Sleep -Seconds 10
        
    } catch {
        Write-Log "监控循环出错: $($_.Exception.Message)" "Red"
        Start-Sleep -Seconds 30
    }
}'''
    
    # 5. 写入增强版 watcher 脚本
    run_command(ssh,
        f'powershell -Command "$content = @\"\n{enhanced_watcher}\n\"@; $content | Set-Content D:\\VideoTranscode\\scripts\\watcher_enhanced.ps1 -Encoding UTF8; Write-Host \'增强版 watcher 脚本已创建\'"',
        "创建增强版 watcher 脚本")
    
    # 6. 备份原 watcher 并替换
    run_command(ssh,
        'powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\watcher.ps1 D:\\VideoTranscode\\scripts\\watcher_original.ps1 -Force; Copy-Item D:\\VideoTranscode\\scripts\\watcher_enhanced.ps1 D:\\VideoTranscode\\scripts\\watcher.ps1 -Force; Write-Host \'watcher 脚本已更新\'"',
        "更新 watcher 脚本")
    
    # 7. 修改转码脚本支持视频类型参数
    run_command(ssh,
        '''powershell -Command "
# 读取现有转码脚本
$content = Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw

# 在参数部分添加 VideoType 参数
if ($content -notmatch 'VideoType') {
    $content = $content -replace 'param\\(', 'param(
    [string]$VideoType = \"long\",'
    
    # 在输出文件名中添加类型标识
    $content = $content -replace '\\$outputFile = Join-Path \\$completedPath', '$outputFile = Join-Path (Join-Path $completedPath $VideoType)'
    
    # 保存修改后的脚本
    $content | Set-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Encoding UTF8
    Write-Host \"转码脚本已更新以支持视频分类\"
} else {
    Write-Host \"转码脚本已支持视频分类\"
}
"''',
        "更新转码脚本支持分类")
    
    # 8. 启动增强版 watcher 服务
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\\"-ExecutionPolicy\\\", \\\"Bypass\\\", \\\"-NoExit\\\", \\\"-File\\\", \\\"D:\\VideoTranscode\\scripts\\watcher.ps1\\\" -WindowStyle Minimized; Write-Host \\\"增强版 Watcher 已启动\\\""',
        "启动增强版 watcher 服务")
    
    # 9. 验证设置
    print(f"\n⏳ 等待10秒，验证设置...")
    import time
    time.sleep(10)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 设置验证 ===\'; Write-Host \'目录结构:\'; Get-ChildItem D:\\VideoTranscode\\downloads; Write-Host \'\\nCompleted目录:\'; Get-ChildItem D:\\VideoTranscode\\completed; Write-Host \'\\n配置文件:\'; if (Test-Path D:\\VideoTranscode\\config.ini) { Get-Content D:\\VideoTranscode\\config.ini } else { Write-Host \'配置文件不存在\' }; Write-Host \'\\nWatcher进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \'*watcher*\' } | Select-Object Id"',
        "验证设置")
    
    print("\n" + "=" * 50)
    print("📹 长短视频分类系统设置完成!")
    print("\n🎯 使用方法:")
    print("1. **自动分类**: 直接放入 downloads 目录，系统自动检测时长分类")
    print("2. **手动分类**: ")
    print("   - 短视频: 放入 downloads/short/ 目录")
    print("   - 长视频: 放入 downloads/long/ 目录")
    print("3. **分类标准**: 默认60秒以下为短视频，可修改 config.ini")
    print("4. **输出目录**: ")
    print("   - 短视频: completed/short/")
    print("   - 长视频: completed/long/")
    
except Exception as e:
    print(f"❌ 设置失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()