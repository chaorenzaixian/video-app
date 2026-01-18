#!/usr/bin/env python3
"""更新 watcher 到 v2 版本"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print("🔄 更新 Watcher 到 v2")
print("=" * 60)

# 停止现有进程
print("🛑 停止现有 watcher...")
ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
time.sleep(2)

# 检查脚本是否存在
print("\n📋 检查脚本...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\scripts\\*.ps1 /b', timeout=30)
files = stdout.read().decode('gbk', errors='ignore').strip()
print(f"  脚本文件: {files}")

# 检查 transcode_v2.ps1 内容
stdin, stdout, stderr = ssh.exec_command('powershell -Command "(Get-Content D:\\VideoTranscode\\scripts\\transcode_v2.ps1 -Head 5) -join \"`n\""', timeout=30)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"\n📄 transcode_v2.ps1 开头:")
print(content[:200] if content else "(空)")

# 检查 watcher.ps1 内容
stdin, stdout, stderr = ssh.exec_command('powershell -Command "(Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 -Head 5) -join \"`n\""', timeout=30)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"\n📄 watcher.ps1 开头:")
print(content[:200] if content else "(空)")

# 更新计划任务指向新脚本
print("\n🔧 更新计划任务...")
update_cmd = '''
schtasks /Delete /TN "VideoWatcherService" /F 2>nul
schtasks /Create /TN "VideoWatcherService" /TR "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1" /SC ONSTART /RU Administrator /RP jCkMIjNlnSd7f6GM /F
'''
stdin, stdout, stderr = ssh.exec_command(update_cmd, timeout=30)
stdout.read()

# 启动新 watcher
print("🚀 启动新 watcher...")
ssh.exec_command('schtasks /Run /TN "VideoWatcherService"', timeout=30)
time.sleep(3)

# 验证
stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
output = stdout.read().decode('gbk', errors='ignore')

if 'powershell.exe' in output:
    print("✅ Watcher v2 正在运行!")
else:
    print("⚠️ 直接启动...")
    ssh.exec_command('start "" powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)

# 等待并检查日志
time.sleep(5)
print("\n📝 最新日志:")
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10 -ErrorAction SilentlyContinue"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
print(log if log else "(无日志)")

ssh.close()
print("\n✅ 完成!")
