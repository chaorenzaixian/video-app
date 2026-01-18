#!/usr/bin/env python3
"""调试watcher扫描逻辑"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 读取watcher脚本的扫描部分
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\scripts\\watcher.ps1', 'r') as f:
    content = f.read().decode('utf-8', errors='ignore')
sftp.close()

# 找到扫描目录的配置
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'inputDir' in line.lower() or 'input' in line.lower() and ('=' in line or 'path' in line.lower()):
        print(f'Line {i+1}: {line.strip()}')

# 检查config.ini
print('\n\nconfig.ini内容:')
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\config.ini')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查watcher是否在扫描正确的目录
print('\n检查watcher脚本中的目录配置:')
for i, line in enumerate(lines[:50]):  # 前50行通常包含配置
    if line.strip() and not line.strip().startswith('#'):
        print(f'{i+1}: {line}')

ssh.close()
