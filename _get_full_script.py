#!/usr/bin/env python3
"""获取完整脚本内容"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 获取脚本列表
print('脚本文件列表:')
stdin, stdout, stderr = ssh.exec_command('cmd /c dir D:\\VideoTranscode\\scripts /b', timeout=30)
output = stdout.read().decode('gbk', errors='replace').strip()
print(output)

# 获取watcher.ps1内容
print('\n' + '=' * 70)
print('watcher.ps1 内容:')
print('=' * 70)
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 -TotalCount 200"', timeout=60)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(output)

ssh.close()
