#!/usr/bin/env python3
"""启动 watcher v2"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print("🚀 启动 Watcher v2")

# 先停止所有 PowerShell
print("停止现有进程...")
ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
time.sleep(2)

# 使用计划任务启动
print("通过计划任务启动...")
ssh.exec_command('schtasks /Run /TN "VideoWatcherService" 2>nul', timeout=30)
time.sleep(3)

# 检查进程
print("\n检查进程...")
stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO LIST', timeout=30)
output = stdout.read().decode('gbk', errors='ignore')

if 'powershell.exe' in output.lower():
    print("✅ Watcher 正在运行!")
else:
    print("⚠️ 尝试直接启动...")
    # 直接启动
    ssh.exec_command('start "" powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)
    time.sleep(3)
    
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO LIST', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore')
    
    if 'powershell.exe' in output.lower():
        print("✅ Watcher 已启动!")
    else:
        print("❌ 启动失败")

# 检查日志
print("\n📝 最新日志:")
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 -ErrorAction SilentlyContinue"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
if log:
    print(log)
else:
    print("(无日志)")

ssh.close()
