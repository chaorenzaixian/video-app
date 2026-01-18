#!/usr/bin/env python3
"""监控多封面测试"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

test_name = "multi_cover_test_1768653313"

print(f'监控视频: {test_name}')
print('=' * 50)

# 检查downloads/short目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\downloads\\short\\{test_name}*" 2>nul')
downloads = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Downloads目录: {downloads if downloads else "(空)"}')

# 检查processing目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{test_name}*" 2>nul')
processing = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Processing目录: {processing if processing else "(空)"}')

# 检查completed目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\completed\\short\\{test_name}" 2>nul')
completed = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Completed目录: {completed if completed else "(空)"}')

# 检查封面目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\completed\\short\\{test_name}\\covers" 2>nul')
covers = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Covers目录: {covers if covers else "(空)"}')

# 检查最新日志
print('\n最新日志:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 15"')
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
