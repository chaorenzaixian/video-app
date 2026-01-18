#!/usr/bin/env python3
"""部署admin.py修复"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

print("连接...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)

sftp = ssh.open_sftp()

# 1. 上传修复后的admin.py
print("1. 上传admin.py...")
with open('backend/app/api/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

temp_path = 'D:\\temp_admin.py'
with sftp.file(temp_path, 'w') as f:
    f.write(content)

scp_cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no "{temp_path}" root@{MAIN_HOST}:/www/wwwroot/video-app/backend/app/api/admin.py'
stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=60)
err = stderr.read().decode()
if 'Permission denied' in err:
    print(f"   ERROR: {err}")
else:
    print("   OK")

# 清理
ssh.exec_command(f'del "{temp_path}"')
sftp.close()

# 2. 重启后端
print("2. 重启后端...")
run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "systemctl restart video-app-backend"'
stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
time.sleep(3)

# 3. 检查状态
print("3. 检查状态...")
run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "systemctl status video-app-backend | head -5"'
stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
print(stdout.read().decode())

ssh.close()
print("完成!")
