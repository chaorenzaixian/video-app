#!/usr/bin/env python3
"""安装依赖并重启服务"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('1. 安装 asyncssh...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cd /www/wwwroot/video-app/backend && source venv/bin/activate && pip install asyncssh==2.14.2"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
print(stdout.read().decode('utf-8', errors='ignore'))

print('\n2. 重启后端服务...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl restart video-app-backend.service"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='ignore'))

time.sleep(5)

print('\n3. 检查服务状态...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl status video-app-backend.service | head -10"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))

print('\n4. 重新构建前端...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cd /www/wwwroot/video-app/frontend && npm run build 2>&1 | tail -20"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
print(stdout.read().decode('utf-8', errors='ignore'))

print('\n5. 测试API...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/health"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
print('\n✅ 完成!')
