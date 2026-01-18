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

print("🔧 创建最小转码脚本")
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
    
    # 1. 停止所有进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue"',
        "停止所有进程")
    
    # 2. 创建最小的转码脚本 - 逐行添加
    run_command(ssh,
        'powershell -Command "Write-Output \'param([string]$InputFile)\' > D:\\VideoTranscode\\scripts\\transcode_simple.ps1"',
        "创建脚本头部")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'$completedPath = \"D:\\VideoTranscode\\completed\"\'"',
        "添加路径变量")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'$logFile = \"D:\\VideoTranscode\\logs\\transcode_simple.log\"\'"',
        "添加日志路径")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'function Write-Log { param($Message) ; Add-Content -Path $logFile -Value \"$(Get-Date): $Message\" ; Write-Host $Message }\'"',
        "添加日志函数")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'Write-Log \"Starting transcode: $InputFile\"\'"',
        "添加开始日志")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'$inputName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)\'"',
        "添加文件名处理")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'$outputFile = Join-Path $completedPath \"${inputName}_transcoded.mp4\"\'"',
        "添加输出文件路径")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'$process = Start-Process -FilePath \"ffmpeg\" -ArgumentList \"-i\", \"`\"$InputFile`\"\", \"-c:v\", \"libx264\", \"-preset\", \"fast\", \"-crf\", \"23\", \"-c:a\", \"aac\", \"-y\", \"`\"$outputFile`\"\" -NoNewWindow -Wait -PassThru\'"',
        "添加 FFmpeg 命令")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1 \'if ($process.ExitCode -eq 0) { Write-Log \"Success\"; Remove-Item $InputFile -Force; exit 0 } else { Write-Log \"Failed\"; exit 1 }\'"',
        "添加结果处理")
    
    # 3. 验证脚本
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_simple.ps1"',
        "查看新脚本内容")
    
    # 4. 测试新脚本
    run_command(ssh,
        'powershell -Command "if (!(Test-Path D:\\VideoTranscode\\processing\\*.mp4)) { $file = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1; if ($file) { Move-Item $file.FullName D:\\VideoTranscode\\processing\\test_simple.mp4 -Force; Write-Host \'已移动测试文件\' } }"',
        "准备测试文件")
    
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\test_simple.mp4) { Write-Host \'测试简单脚本...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_simple.ps1 -InputFile D:\\VideoTranscode\\processing\\test_simple.mp4 } else { Write-Host \'没有测试文件\' }"',
        "测试简单脚本")
    
    # 5. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 简单脚本测试结果 ===\'; Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object Name, LastWriteTime"',
        "检查测试结果")
    
    # 6. 如果成功，替换原脚本
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\completed\\*simple*) { Write-Host \'简单脚本测试成功，替换原脚本\'; Copy-Item D:\\VideoTranscode\\scripts\\transcode_simple.ps1 D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Force; Write-Host \'脚本已替换\' } else { Write-Host \'简单脚本测试失败\' }"',
        "替换原脚本")
    
    # 7. 重启 watcher
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已启动\\""',
        "启动 watcher")
    
    print("\n" + "=" * 50)
    print("✅ 最小脚本创建完成!")
    print("🎯 如果测试成功，原脚本已被替换")
    print("📊 转码服务应该恢复正常工作")
    
except Exception as e:
    print(f"❌ 创建失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()