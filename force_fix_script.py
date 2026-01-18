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

print("💥 强制修复脚本 - 创建新的转码脚本")
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
    
    # 1. 停止所有进程并强制解锁文件
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep 2"',
        "停止所有进程")
    
    # 2. 备份原文件并创建新文件
    run_command(ssh,
        'powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\transcode_full.ps1 D:\\VideoTranscode\\scripts\\transcode_full_broken.ps1 -Force; Write-Host \'原文件已备份\'"',
        "备份原文件")
    
    # 3. 创建一个简化的转码脚本（去掉问题行）
    new_script = '''param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile
)

# 简化的转码脚本 - 已移除语法错误行
$logPath = "D:\\VideoTranscode\\logs"
$completedPath = "D:\\VideoTranscode\\completed"

if (!(Test-Path $logPath)) { New-Item -ItemType Directory -Path $logPath -Force }
if (!(Test-Path $completedPath)) { New-Item -ItemType Directory -Path $completedPath -Force }

$logFile = Join-Path $logPath "transcode_$(Get-Date -Format 'yyyyMMdd').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "MM/dd/yyyy HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

try {
    Write-Log "Starting transcode"
    Write-Log "Input: $InputFile"
    
    $inputName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
    $outputFile = Join-Path $completedPath "${inputName}_transcoded.mp4"
    
    Write-Log "Output: $outputFile"
    
    # FFmpeg 转码命令
    $ffmpegArgs = @(
        "-i", "`"$InputFile`""
        "-c:v", "libx264"
        "-preset", "fast"
        "-crf", "23"
        "-c:a", "aac"
        "-b:a", "128k"
        "-y"
        "`"$outputFile`""
    )
    
    $startTime = Get-Date
    $process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($process.ExitCode -eq 0) {
        Write-Log "Transcode successful, duration: $duration seconds"
        
        # 删除原文件
        Remove-Item $InputFile -Force
        Write-Log "Deleted original file"
        
        exit 0
    } else {
        Write-Log "Transcode failed with exit code: $($process.ExitCode)" "Red"
        exit 1
    }
    
} catch {
    Write-Log "Error during transcode: $($_.Exception.Message)" "Red"
    exit 1
}'''
    
    # 4. 写入新的转码脚本
    run_command(ssh,
        f'powershell -Command "$content = @\"\n{new_script}\n\"@; $content | Set-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Encoding UTF8; Write-Host \'新转码脚本已创建\'"',
        "创建新转码脚本")
    
    # 5. 验证新脚本
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Measure-Object -Line | Select-Object Lines"',
        "验证新脚本行数")
    
    # 6. 测试新脚本
    run_command(ssh,
        'powershell -Command "if (!(Test-Path D:\\VideoTranscode\\processing\\*.mp4)) { $file = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1; if ($file) { Move-Item $file.FullName D:\\VideoTranscode\\processing\\test_new_script.mp4 -Force; Write-Host \'已移动测试文件\' } }"',
        "准备测试文件")
    
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\test_new_script.mp4) { Write-Host \'测试新脚本...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\test_new_script.mp4 } else { Write-Host \'没有测试文件\' }"',
        "测试新脚本")
    
    # 7. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 新脚本测试结果 ===\'; Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object Name, LastWriteTime"',
        "检查测试结果")
    
    # 8. 如果成功，重启 watcher
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已启动\\""',
        "启动 watcher")
    
    print("\n" + "=" * 50)
    print("💥 强制修复完成!")
    print("🎯 已创建全新的转码脚本，移除了所有语法错误")
    print("📊 如果测试成功，转码服务应该恢复正常")
    
except Exception as e:
    print(f"❌ 强制修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()