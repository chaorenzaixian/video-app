#!/usr/bin/env python3
"""验证当前状态"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("当前待处理视频:")
print("=" * 60)
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT id, title, hls_url FROM videos WHERE status = 'REVIEWING' ORDER BY id;\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

print("\n视频统计:")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT status, COUNT(*) FROM videos GROUP BY status;\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

ssh.close()
