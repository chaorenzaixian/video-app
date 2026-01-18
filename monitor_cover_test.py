#!/usr/bin/env python3
"""监控封面测试转码进度"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

test_name = "cover_test_1768652638"

print(f'监控视频: {test_name}')
print('=' * 50)

# 检查input目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\input\\{test_name}*" 2>nul')
input_files = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Input目录: {input_files if input_files else "(空)"}')

# 检查processing目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{test_name}*" 2>nul')
processing_files = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Processing目录: {processing_files if processing_files else "(空)"}')

# 检查completed目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\completed\\short\\{test_name}*" 2>nul')
completed_files = stdout.read().decode('gbk', errors='ignore').strip()
print(f'Completed目录: {completed_files if completed_files else "(空)"}')

# 检查封面目录
stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\completed\\short\\{test_name}\\*" 2>nul')
cover_files = stdout.read().decode('gbk', errors='ignore').strip()
print(f'封面目录: {cover_files if cover_files else "(空)"}')

# 检查最新日志
print('\n最新日志:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"')
log = stdout.read().decode('utf-8', errors='ignore')
print(log)

ssh.close()
