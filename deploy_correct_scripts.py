#!/usr/bin/env python3
import paramiko
import sys
import base64

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

# 正确的简化转码脚本（没有 $([math]::Round) 语法错误）
CORRECT_TRANSCODE_SCRIPT = '''# 简化转码脚本 - 无语法错误版本
param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile
)

$ErrorActionPreference = "Continue"
$logFile = "D:\\VideoTranscode\\logs\\transcode.log"
$completedPath = "D:\\VideoTranscode\\completed"

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Message"
    Add-Content -Path $logFile -Value $logMessage
    Write-Host $logMessage
}

Write-Log "Starting transcode"
Write-Log "Input: $InputFile"

# 生成输出文件名
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
$outputFile = Join-Path $completedPath "${baseName}_transcoded.mp4"

Write-Log "Output: $outputFile"

# 检测是否有NVIDIA GPU
$hasNvenc = $false
try {
    $nvencTest = & ffmpeg -hide_banner -encoders 2>&1 | Select-String "h264_nvenc"
    if ($nvencTest) { $hasNvenc = $true }
} catch {}

# 转码
$startTime = Get-Date

if ($hasNvenc) {
    Write-Log "Using GPU (NVENC)"
    $ffmpegArgs = @(
        "-hwaccel", "cuda",
        "-i", $InputFile,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-y",
        $outputFile
    )
} else {
    Write-Log "Using CPU"
    $ffmpegArgs = @(
        "-i", $InputFile,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-y",
        $outputFile
    )
}

$process = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($process.ExitCode -eq 0 -and (Test-Path $outputFile)) {
    $durationRounded = [math]::Round($duration, 2)
    Write-Log "Transcode successful, duration: $durationRounded seconds"
    
    # 删除原文件
    if (Test-Path $InputFile) {
        Remove-Item $InputFile -Force
        Write-Log "Deleted original file"
    }
    
    exit 0
} else {
    Write-Log "Transcode failed! Exit code: $($process.ExitCode)"
    exit 1
}
'''

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
                print(f"   {output[:200]}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error[:200]}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("🚀 部署正确的转码脚本")
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
    
    # 1. 停止 watcher
    run_command(ssh,
        'powershell -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like \'*watcher*\' } | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \'已停止 watcher\'"',
        "停止 watcher")
    
    import time
    time.sleep(3)
    
    # 2. 备份旧脚本
    run_command(ssh,
        'powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\transcode_full.ps1 D:\\VideoTranscode\\scripts\\transcode_full.ps1.old -Force -ErrorAction SilentlyContinue; Write-Host \'已备份\'"',
        "备份旧脚本")
    
    # 3. 使用 Base64 编码部署新脚本
    print("\n📋 部署新的转码脚本...")
    script_bytes = CORRECT_TRANSCODE_SCRIPT.encode('utf-8')
    script_base64 = base64.b64encode(script_bytes).decode('ascii')
    
    deploy_cmd = f'powershell -Command "$bytes = [System.Convert]::FromBase64String(\'{script_base64}\'); $content = [System.Text.Encoding]::UTF8.GetString($bytes); $content | Set-Content -Path D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Encoding UTF8; Write-Host \'脚本已部署\'"'
    
    run_command(ssh, deploy_cmd, "部署新脚本")
    
    # 4. 验证语法
    run_command(ssh,
        'powershell -Command "$errors = $null; $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw), [ref]$errors); if ($errors.Count -eq 0) { Write-Host \'✅ 语法正确\' } else { Write-Host \'❌ 语法错误:\'; $errors | Select-Object -First 3 Message }"',
        "验证语法")
    
    # 5. 重启 watcher
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy\', \'Bypass\', \'-NoExit\', \'-File\', \'D:\\VideoTranscode\\scripts\\watcher.ps1\' -WindowStyle Minimized; Write-Host \'Watcher 已启动\'"',
        "启动 watcher")
    
    time.sleep(5)
    
    # 6. 验证 watcher 运行
    run_command(ssh,
        'powershell -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like \'*watcher*\' } | Select-Object Id, StartTime"',
        "验证 watcher")
    
    print("\n" + "=" * 50)
    print("✅ 部署完成!")
    print("\n📝 新脚本特点:")
    print("- 移除了所有 $([math]::Round) 语法错误")
    print("- 简化了转码流程")
    print("- 支持 GPU 和 CPU 转码")
    print("- 自动删除原文件")
    print("\n现在可以测试转码功能了")
    
except Exception as e:
    print(f"❌ 部署失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
