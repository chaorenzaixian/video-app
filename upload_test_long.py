#!/usr/bin/env python3
"""手动上传 test_long 到主服务器并调试"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('📤 手动上传 test_long')
print('=' * 60)

# 1. 先在主服务器创建目录
print('\n1. 创建主服务器目录...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL root@38.47.218.137 "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/test_long"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 2. 上传 HLS 目录
print('\n2. 上传 HLS 目录...')
cmd = 'scp -r -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\VideoTranscode\\completed\\long\\test_long\\hls\\*" root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/hls/test_long/'
print(f'  命令: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 3. 上传封面
print('\n3. 上传封面...')
cmd = 'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\VideoTranscode\\completed\\long\\test_long\\test_long.webp" root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/thumbnails/'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 4. 上传预览
print('\n4. 上传预览...')
cmd = 'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\VideoTranscode\\completed\\long\\test_long\\test_long_preview.webm" root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/previews/'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 5. 验证上传
print('\n5. 验证上传...')
time.sleep(2)
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/hls/test_long/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
print(f'  HLS目录: {out}')

cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/thumbnails/test_long.webp"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
print(f'  封面: {out}')

cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/previews/test_long_preview.webm"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
print(f'  预览: {out}')

ssh.close()
print('\nDone!')
