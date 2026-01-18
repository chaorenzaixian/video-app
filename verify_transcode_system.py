#!/usr/bin/env python3
"""验证转码系统状态"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("=" * 60)
print("转码系统状态检查")
print("=" * 60)

# 1. 检查 watcher 进程
print("\n1. Watcher 进程状态:")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'powershell' in output.lower():
    print("   ✓ PowerShell 进程运行中")
    print(f"   {output.strip()}")
else:
    print("   ✗ 未检测到 PowerShell 进程")

# 2. 检查最近的 watcher 日志
print("\n2. 最近的 Watcher 日志 (最后20行):")
cmd = 'powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

# 3. 检查待处理文件
print("\n3. 待处理视频文件:")
print("   短视频目录 (downloads/short):")
cmd = 'dir /b D:\\VideoTranscode\\downloads\\short 2>nul || echo (空)'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(f"   {output if output else '(空)'}")

print("\n   长视频目录 (downloads/long):")
cmd = 'dir /b D:\\VideoTranscode\\downloads\\long 2>nul || echo (空)'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(f"   {output if output else '(空)'}")

# 4. 检查正在处理的文件
print("\n4. 正在处理的文件 (processing):")
cmd = 'dir /b D:\\VideoTranscode\\processing 2>nul || echo (空)'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(f"   {output if output else '(空)'}")

# 5. 检查已完成的文件
print("\n5. 最近完成的视频:")
cmd = 'dir /b /o-d D:\\VideoTranscode\\completed\\short 2>nul | more +0 < nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
short_output = stdout.read().decode('utf-8', errors='replace').strip()

cmd = 'dir /b /o-d D:\\VideoTranscode\\completed\\long 2>nul | more +0 < nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
long_output = stdout.read().decode('utf-8', errors='replace').strip()

print(f"   短视频: {short_output[:200] if short_output else '(空)'}")
print(f"   长视频: {long_output[:200] if long_output else '(空)'}")

# 6. 验证 watcher 脚本是否包含 UTF-8 修复
print("\n6. Watcher 脚本 UTF-8 编码修复验证:")
cmd = 'powershell -Command "Select-String -Path D:\\VideoTranscode\\scripts\\watcher.ps1 -Pattern \'WebRequest|charset=utf-8|UTF8\' | Select-Object -First 3"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'WebRequest' in output or 'charset=utf-8' in output or 'UTF8' in output:
    print("   ✓ 脚本包含 UTF-8 编码修复")
else:
    print("   ✗ 脚本可能未包含 UTF-8 修复")

ssh.close()

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
