#!/usr/bin/env python3
"""检查转码服务器上当前的脚本"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('=' * 70)
print('检查转码服务器上的脚本')
print('=' * 70)

# 查看transcode_full.ps1的内容
print('\n1. transcode_full.ps1 内容:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1"', timeout=60)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(output[:5000])

ssh.close()
