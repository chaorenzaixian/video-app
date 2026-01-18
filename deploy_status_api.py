#!/usr/bin/env python3
"""部署状态API到转码服务器"""
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
print('✓ 状态API脚本已上传')

# 安装Flask（如果没有）
print('\n安装Flask...')
stdin, stdout, stderr = ssh.exec_command('pip install flask', timeout=120)
print(stdout.read().decode('utf-8', errors='ignore'))

# 创建启动脚本
start_script = '''@echo off
cd /d D:\\VideoTranscode
python status_api.py
'''
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\start_status_api.bat', 'w') as f:
    f.write(start_script)
sftp.close()
print('✓ 启动脚本已创建')

# 创建VBS隐藏启动脚本
vbs_script = '''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "D:\\VideoTranscode\\start_status_api.bat" & chr(34), 0
Set WshShell = Nothing
'''
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\start_status_api_hidden.vbs', 'w') as f:
    f.write(vbs_script)
sftp.close()
print('✓ 隐藏启动脚本已创建')

# 停止可能存在的旧进程
print('\n停止旧进程...')
stdin, stdout, stderr = ssh.exec_command('taskkill /f /fi "windowtitle eq status_api*" 2>nul')
time.sleep(1)

# 启动状态API
print('\n启动状态API...')
stdin, stdout, stderr = ssh.exec_command('wscript "D:\\VideoTranscode\\start_status_api_hidden.vbs"')
time.sleep(3)

# 测试API
print('\n测试API...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/health')
health = stdout.read().decode('utf-8', errors='ignore')
print(f'健康检查: {health}')

if 'ok' in health:
    print('\n✅ 状态API已成功启动!')
else:
    print('\n⚠️ 状态API可能未正常启动，请检查')

ssh.close()
