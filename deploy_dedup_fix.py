#!/usr/bin/env python3
"""部署去重修复"""
import paramiko
import os

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

# 读取本地文件
with open('backend/app/api/admin_video_ops.py', 'r', encoding='utf-8') as f:
    content = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("部署去重修复...")
print("=" * 60)

# 写入临时文件
temp_file = 'D:\\VideoTranscode\\temp_admin_video_ops.py'
sftp = ssh.open_sftp()
with sftp.file(temp_file, 'w') as f:
    f.write(content)
sftp.close()

# 上传到主服务器
print("上传到主服务器...")
cmd = f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no "{temp_file}" {MAIN_USER}@{MAIN_HOST}:/www/wwwroot/video-app/backend/app/api/admin_video_ops.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
stdout.read()
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print(f"上传错误: {err}")

# 重启后端服务
print("重启后端服务...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cd /www/wwwroot/video-app/backend && supervisorctl restart video-api"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

# 清理临时文件
cmd = f'del "{temp_file}"'
ssh.exec_command(cmd, timeout=30)

ssh.close()
print("\n完成!")
