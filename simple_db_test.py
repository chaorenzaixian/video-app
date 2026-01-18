#!/usr/bin/env python3
"""简单数据库测试"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 简单SQL测试
tests = [
    "SELECT id, username, role FROM users WHERE role = 'USER' LIMIT 3;",
    "SELECT id, username, role FROM users WHERE role = 'ADMIN' LIMIT 3;",
    "SELECT id, username, role FROM users WHERE role::text = 'USER' LIMIT 3;",
]

for sql in tests:
    print(f"\n测试: {sql}")
    cmd = f"PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -t -c \\\"{sql}\\\""
    run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} {cmd}'
    stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(f"结果: {output.strip()}")
    if error:
        print(f"错误: {error}")

ssh.close()
