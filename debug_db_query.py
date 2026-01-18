#!/usr/bin/env python3
"""调试数据库查询"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 测试简单查询
print("测试1: 简单计数")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -c \'SELECT COUNT(*) FROM videos;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
error = stderr.read().decode('utf-8', errors='replace')
print(f"Output: {output}")
print(f"Error: {error}")

print("\n测试2: 最新视频ID")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -c \'SELECT MAX(id) FROM videos;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"Output: {output}")

print("\n测试3: 查看videos表结构")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -c \'\\\\d videos\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"Output: {output[:2000]}")

ssh.close()
