#!/usr/bin/env python3
"""查询视频"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 使用 -t 选项只输出数据
print("查询最新视频（使用-t选项）:")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -t -c \'SELECT id, title FROM videos ORDER BY id DESC LIMIT 10;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"Output:\n{output}")

# 查询ID > 100的视频
print("\n查询ID > 100的视频:")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -t -c \'SELECT id, title FROM videos WHERE id > 100;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"Output:\n{output}")

# 查询所有视频的ID和标题
print("\n所有视频:")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -t -c \'SELECT id, title FROM videos ORDER BY id;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"Output:\n{output}")

ssh.close()
