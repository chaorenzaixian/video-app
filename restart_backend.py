#!/usr/bin/env python3
"""重启后端服务"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("重启后端服务...")
print("=" * 60)

# 检查当前状态
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "netstat -tlnp | grep -E \\"5000|8000\\""'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"当前端口状态:\n{output}")

# 重启服务
print("\n重启 video-app-backend 服务...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "systemctl restart video-app-backend.service"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
time.sleep(5)

# 检查状态
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "systemctl status video-app-backend.service"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"\n服务状态:\n{output}")

# 等待服务启动
print("\n等待服务启动...")
time.sleep(5)

# 检查端口
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "netstat -tlnp | grep -E \\"5000|8000\\""'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"端口状态:\n{output}")

# 测试 API
print("\n测试 API...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "curl -s http://localhost:5000/api/v1/health 2>&1 || curl -s http://localhost:8000/api/v1/health 2>&1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"健康检查: {output}")

ssh.close()
print("\n完成")
