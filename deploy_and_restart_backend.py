#!/usr/bin/env python3
"""部署后端更新并重启服务"""
import paramiko
import os

MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
MAIN_KEY = 'server_key'  # 当前目录下的密钥文件
BACKEND_PATH = '/www/wwwroot/video-app/backend'

print("连接主服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 使用密钥连接
key = paramiko.Ed25519Key.from_private_key_file(MAIN_KEY)
ssh.connect(MAIN_HOST, username=MAIN_USER, pkey=key, timeout=30)
print("✓ 已连接")

sftp = ssh.open_sftp()

# 1. 上传transcode_monitor.py
print("\n1. 上传 transcode_monitor.py...")
local_file = 'backend/app/api/transcode_monitor.py'
remote_file = f'{BACKEND_PATH}/app/api/transcode_monitor.py'

try:
    sftp.put(local_file, remote_file)
    print(f"   ✓ 已上传")
except Exception as e:
    print(f"   ✗ 上传失败: {e}")

# 2. 检查__init__.py是否需要更新
print("\n2. 检查 __init__.py...")
stdin, stdout, stderr = ssh.exec_command(f'grep -c "transcode_monitor" {BACKEND_PATH}/app/api/__init__.py')
count = stdout.read().decode().strip()
if count and int(count) > 0:
    print(f"   ✓ transcode_monitor 已在 __init__.py 中注册")
else:
    print("   需要更新 __init__.py")
    sftp.put('backend/app/api/__init__.py', f'{BACKEND_PATH}/app/api/__init__.py')
    print("   ✓ 已更新")

# 3. 重启后端服务
print("\n3. 重启后端服务...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart video-app-backend')
err = stderr.read().decode()
if err:
    print(f"   警告: {err}")
else:
    print("   ✓ 服务重启命令已发送")

# 等待服务启动
import time
time.sleep(3)

# 4. 检查服务状态
print("\n4. 检查服务状态...")
stdin, stdout, stderr = ssh.exec_command('systemctl status video-app-backend | head -20')
status = stdout.read().decode()
print(status)

# 5. 测试API
print("\n5. 测试转码监控API...")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/api/admin/transcode/status -H "X-Transcode-Key: test" | head -100')
response = stdout.read().decode()
print(f"   响应: {response[:200]}...")

sftp.close()
ssh.close()
print("\n部署完成")
