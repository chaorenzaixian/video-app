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

print("📊 最终状态检查")
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
    
    # 1. 检查当前系统状态
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 系统当前状态 ===\'; Write-Host \'当前时间:\' (Get-Date); Write-Host \'\\nDownloads目录:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name, @{Name=\'Size(MB)\';Expression={[math]::Round($_.Length/1MB,2)}}; Write-Host \'\\nProcessing目录:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted目录 (最新5个):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Select-Object Name, LastWriteTime"',
        "检查系统状态")
    
    # 2. 检查进程状态
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 进程状态 ===\'; Write-Host \'PowerShell进程:\'; Get-Process powershell | Select-Object Id, ProcessName, StartTime; Write-Host \'\\nWatcher进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \'*watcher*\' } | Select-Object Id, StartTime"',
        "检查进程状态")
    
    # 3. 检查最新日志
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 最新日志 ===\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Write-Host \'Watcher日志 (最后10行):\'; Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10 } else { Write-Host \'Watcher日志不存在\' }; Write-Host \'\\n转码日志:\'; Get-ChildItem D:\\VideoTranscode\\logs -Filter \'transcode*.log\' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { Write-Host \'最新转码日志:\'; Get-Content $_.FullName -Tail 5 }"',
        "检查最新日志")
    
    # 4. 检查脚本状态
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 脚本状态 ===\'; Write-Host \'transcode_full.ps1 行数:\' (Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Measure-Object -Line).Lines; Write-Host \'transcode_simple.ps1 存在:\' (Test-Path D:\\VideoTranscode\\scripts\\transcode_simple.ps1); Write-Host \'watcher.ps1 存在:\' (Test-Path D:\\VideoTranscode\\scripts\\watcher.ps1)"',
        "检查脚本状态")
    
    # 5. 等待一段时间观察是否有新活动
    print(f"\n⏳ 等待30秒，观察是否有新的处理活动...")
    time.sleep(30)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 30秒后状态 ===\'; Write-Host \'Downloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nProcessing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\n最新日志 (最后3行):\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3 }"',
        "30秒后状态检查")
    
    print("\n" + "=" * 50)
    print("📊 最终状态检查完成!")
    print("\n🔍 总结分析:")
    print("1. 如果 downloads 目录中仍有文件但没有被处理，说明 watcher 有问题")
    print("2. 如果日志中仍有语法错误，说明脚本修复未生效")
    print("3. 如果 completed 目录有新文件，说明转码功能正常")
    print("4. 如果没有 watcher 进程，说明服务没有启动")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()