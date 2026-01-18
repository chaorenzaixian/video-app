#!/usr/bin/env python3
"""重启 watcher"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("重启 Watcher...")

# 1. 先检查当前 PowerShell 进程
print("\n1. 当前 PowerShell 进程:")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   {output.strip() if output.strip() else '无'}")

# 2. 杀掉所有 PowerShell 进程
print("\n2. 停止所有 PowerShell 进程...")
cmd = 'taskkill /F /IM powershell.exe 2>nul & echo Done'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   {output.strip()}")

time.sleep(2)

# 3. 使用计划任务启动 watcher
print("\n3. 启动 Watcher (使用 schtasks)...")
# 先删除旧任务
cmd = 'schtasks /Delete /TN "StartWatcher" /F 2>nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

# 创建新任务立即运行
cmd = 'schtasks /Create /TN "StartWatcher" /TR "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1" /SC ONCE /ST 00:00 /F'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   创建任务: {output.strip()}")

# 立即运行
cmd = 'schtasks /Run /TN "StartWatcher"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   运行任务: {output.strip()}")

time.sleep(3)

# 4. 检查是否启动成功
print("\n4. 检查 Watcher 状态...")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'powershell' in output.lower():
    print(f"   ✓ Watcher 已启动")
    print(f"   {output.strip()}")
else:
    print("   ✗ Watcher 未启动，尝试其他方式...")
    # 尝试使用 WMI
    cmd = 'wmic process call create "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"   WMI: {output.strip()}")

time.sleep(2)

# 5. 最终检查
print("\n5. 最终状态:")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   PowerShell: {output.strip() if output.strip() else '未运行'}")

# 检查最新日志
cmd = 'powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 -Encoding UTF8"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"\n   最新日志:\n{output}")

ssh.close()
