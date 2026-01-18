#!/usr/bin/env python3
"""调试 SCP 方法"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('🔍 调试 SCP 方法')
print('=' * 60)

# 方法1: 直接调用 scp
print('\n方法1: 直接调用 scp')
cmd = '''powershell -Command "& scp -i 'C:\\server_key' -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL 'D:\\VideoTranscode\\completed\\short\\test_flow\\test_flow.mp4' root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/shorts/"'''
print(f'  命令: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 验证
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/shorts/test_flow.mp4 2>/dev/null"', timeout=60)
out = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  验证: {out if out else "(not found)"}')

# 方法2: 使用 cmd /c
print('\n方法2: 使用 cmd /c')
cmd = '''cmd /c "scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL D:\\VideoTranscode\\completed\\short\\test_flow\\test_flow.webp root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/thumbnails/"'''
print(f'  命令: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 验证
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/thumbnails/test_flow.webp 2>/dev/null"', timeout=60)
out = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  验证: {out if out else "(not found)"}')

ssh.close()
print('\nDone!')
