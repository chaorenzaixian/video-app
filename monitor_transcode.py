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
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
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

print("📺 监控转码服务实时状态")
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
    
    # 1. 检查当前状态
    run_command(ssh,
        'powershell -Command "Write-Host \\"=== 当前时间 ===\\"; Get-Date; Write-Host \\"\\n=== Downloads目录 ===\\"; Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" | Select-Object Name, @{Name=\\"Size(MB)\\";Expression={[math]::Round($_.Length/1MB,2)}}, LastWriteTime"',
        "检查当前状态")
    
    # 2. 查看最新日志
    run_command(ssh,
        'powershell -Command "if (Test-Path \\"D:\\VideoTranscode\\logs\\watcher.log\\") { Write-Host \\"=== 最新日志 (最后15行) ===\\"; Get-Content \\"D:\\VideoTranscode\\logs\\watcher.log\\" -Tail 15 } else { Write-Host \\"日志文件不存在\\" }"',
        "查看最新日志")
    
    # 3. 检查进程状态
    run_command(ssh,
        'powershell -Command "Write-Host \\"=== Watcher进程 ===\\"; Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, ProcessName, StartTime, @{Name=\\"Runtime\\";Expression={(Get-Date) - $_.StartTime}}"',
        "检查进程状态")
    
    # 4. 等待并再次检查（看是否有新的处理活动）
    print(f"\n⏳ 等待30秒，观察是否有新的转码活动...")
    time.sleep(30)
    
    run_command(ssh,
        'powershell -Command "Write-Host \\"=== 30秒后的状态 ===\\"; Write-Host \\"Downloads目录:\\"; Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" | Select-Object Name; Write-Host \\"\\nProcessing目录:\\"; Get-ChildItem \\"D:\\VideoTranscode\\processing\\" | Select-Object Name; Write-Host \\"\\n最新日志 (最后5行):\\"; if (Test-Path \\"D:\\VideoTranscode\\logs\\watcher.log\\") { Get-Content \\"D:\\VideoTranscode\\logs\\watcher.log\\" -Tail 5 }"',
        "30秒后状态检查")
    
    print("\n" + "=" * 50)
    print("✅ 监控完成!")
    print("💡 如果看到文件从 downloads 移动到 processing 再消失，说明转码正常工作")
    
except Exception as e:
    print(f"❌ 监控失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()