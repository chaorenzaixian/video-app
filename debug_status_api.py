#!/usr/bin/env python3
"""调试状态API"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 直接运行看错误
print('直接运行status_api.py查看错误...')
stdin, stdout, stderr = ssh.exec_command('cd D:\\VideoTranscode && python status_api.py', timeout=10)
time.sleep(5)

# 检查端口
print('\n检查端口5001:')
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
out = stdout.read().decode('gbk', errors='ignore')
print(out if out else '端口5001未被监听')

# 检查Python进程
print('\nPython进程:')
stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
