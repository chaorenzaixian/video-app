#!/usr/bin/env python3
"""优化 Nginx 视频传输配置"""
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

print("优化 Nginx 视频传输配置...")
print("=" * 60)

# 1. 检查当前 nginx 配置
print("\n1. 当前 Nginx 配置:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cat /www/server/panel/vhost/nginx/0.default.conf"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
current_config = stdout.read().decode('utf-8', errors='replace')
print(current_config)

# 2. 检查 nginx 主配置
print("\n2. Nginx 主配置 (sendfile, tcp_nopush 等):")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "grep -E \'sendfile|tcp_nopush|tcp_nodelay|keepalive|gzip\' /www/server/nginx/conf/nginx.conf"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 3. 检查服务器带宽
print("\n3. 测试服务器出口带宽:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 - --simple 2>/dev/null || echo 带宽测试工具不可用"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("\n检查完成!")
