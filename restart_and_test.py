#!/usr/bin/env python3
import paramiko
import sys
import time

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

print("🔄 重启并测试转码服务")
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
    
    # 1. 检查当前进程状态
    run_command(ssh,
        'powershell -Command "Write-Host \\"所有 PowerShell 进程:\\"; Get-Process powershell | Select-Object Id, ProcessName, StartTime, @{Name=\\"CommandLine\\";Expression={$_.CommandLine}}"',
        "检查所有 PowerShell 进程")
    
    # 2. 强制停止所有可能的 watcher 进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \\"已停止所有 PowerShell 进程\\""',
        "停止所有 PowerShell 进程")
    
    # 3. 等待进程完全停止
    print("\n⏳ 等待3秒...")
    time.sleep(3)
    
    # 4. 手动测试一个文件的转码
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\downloads\\1768543353686.mp4) { Write-Host \'移动文件到处理目录...\'; Move-Item D:\\VideoTranscode\\downloads\\1768543353686.mp4 D:\\VideoTranscode\\processing\\test_manual.mp4 -Force; Write-Host \'文件已移动\' } else { Write-Host \'文件不存在\' }"',
        "手动移动文件进行测试")
    
    # 5. 手动执行转码
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\test_manual.mp4) { Write-Host \'开始手动转码测试...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\test_manual.mp4 } else { Write-Host \'测试文件不存在\' }"',
        "手动执行转码测试")
    
    # 6. 检查转码结果
    run_command(ssh,
        'powershell -Command "Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新3个):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | Select-Object Name, LastWriteTime"',
        "检查转码结果")
    
    # 7. 如果转码成功，启动 watcher
    run_command(ssh,
        'powershell -Command "Write-Host \'启动新的 watcher 服务...\'; Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \'Watcher 已启动\'"',
        "启动 watcher 服务")
    
    # 8. 等待并检查 watcher 是否工作
    print(f"\n⏳ 等待20秒，检查 watcher 是否开始工作...")
    time.sleep(20)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 工作状态 ===\'; Write-Host \'进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, StartTime; Write-Host \'\\nDownloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nProcessing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\n最新日志:\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 }"',
        "检查 watcher 工作状态")
    
    print("\n" + "=" * 50)
    print("✅ 重启和测试完成!")
    print("🎯 如果手动转码成功，说明语法问题已解决")
    print("📁 如果 watcher 正常工作，应该会自动处理剩余文件")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()