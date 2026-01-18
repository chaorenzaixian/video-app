#!/usr/bin/env python3
"""部署状态API到转码服务器 - 使用端口5001"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 读取状态API脚本
with open('transcode_status_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 上传到转码服务器
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\status_api.py', 'w') as f:
    f.write(content)
sftp.close()
print('✓ 状态API脚本已上传 (端口5001)')

# 创建启动脚本
start_script = '''@echo off
cd /d D:\\VideoTranscode
python status_api.py
'''
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\start_status_api.bat', 'w') as f:
    f.write(start_script)
sftp.close()

# 创建VBS隐藏启动脚本
vbs_script = '''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "D:\\VideoTranscode\\start_status_api.bat" & chr(34), 0
Set WshShell = Nothing
'''
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\start_status_api_hidden.vbs', 'w') as f:
    f.write(vbs_script)
sftp.close()

# 启动状态API
print('\n启动状态API (端口5001)...')
stdin, stdout, stderr = ssh.exec_command('wscript "D:\\VideoTranscode\\start_status_api_hidden.vbs"')
time.sleep(3)

# 测试API
print('\n测试API...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
health = stdout.read().decode('utf-8', errors='ignore')
print(f'健康检查: {health}')

if 'ok' in health:
    print('\n✅ 状态API已成功启动在端口5001!')
    
    # 测试状态接口
    print('\n测试状态接口...')
    stdin, stdout, stderr = ssh.exec_command('curl -s -H "X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U" http://localhost:5001/status')
    status = stdout.read().decode('utf-8', errors='ignore')
    print(f'状态: {status[:200]}...')
else:
    print('\n⚠️ 状态API可能未正常启动')

ssh.close()
