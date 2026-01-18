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

print("📺 监控修复结果")
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
    
    # 监控3次，每次间隔30秒
    for i in range(3):
        print(f"\n🔍 第 {i+1} 次检查 (间隔30秒)")
        
        # 检查当前状态
        run_command(ssh,
            'powershell -Command "Write-Host \\"=== 当前时间: $(Get-Date) ===\\"; Write-Host \\"Downloads:\\" ; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name, @{Name=\\"Size(MB)\\";Expression={[math]::Round($_.Length/1MB,2)}}; Write-Host \\"\\nProcessing:\\"; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name"',
            f"检查目录状态 ({i+1}/3)")
        
        # 检查最新日志
        run_command(ssh,
            'powershell -Command "Write-Host \\"最新日志 (最后8行):\\"; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 8 }"',
            f"检查最新日志 ({i+1}/3)")
        
        # 检查进程状态
        run_command(ssh,
            'powershell -Command "Write-Host \\"Watcher进程:\\"; Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, StartTime, @{Name=\\"Runtime\\";Expression={(Get-Date) - $_.StartTime}}"',
            f"检查进程状态 ({i+1}/3)")
        
        if i < 2:  # 不在最后一次等待
            print(f"\n⏳ 等待30秒后进行下一次检查...")
            time.sleep(30)
    
    # 最终总结
    run_command(ssh,
        'powershell -Command "Write-Host \\"=== 最终总结 ===\\"; Write-Host \\"Completed目录 (最新5个):\\"; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Select-Object Name, @{Name=\\"Size(MB)\\";Expression={[math]::Round($_.Length/1MB,2)}}, LastWriteTime"',
        "最终总结")
    
    print("\n" + "=" * 50)
    print("📊 监控完成!")
    print("💡 如果看到新的转码成功记录，说明修复生效")
    print("🚨 如果仍有语法错误，需要进一步检查脚本")
    
except Exception as e:
    print(f"❌ 监控失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()