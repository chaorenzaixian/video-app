#!/usr/bin/env python3
"""验证转码监控API是否正常工作"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("✓ 已连接")

# 1. 检查主服务器后端端口
print("\n1. 检查主服务器后端端口...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "netstat -tlnp | grep python"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode())

# 2. 测试后端健康检查
print("\n2. 测试后端健康检查...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "curl -s http://localhost:8000/api/health"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(f"响应: {stdout.read().decode()}")

# 3. 先登录获取token
print("\n3. 登录获取token...")
login_cmd = f'''ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{{\\"username\\":\\"admin\\",\\"password\\":\\"admin123\\"}}'"'''
stdin, stdout, stderr = ssh.exec_command(login_cmd, timeout=30)
response = stdout.read().decode()
print(f"登录响应: {response[:200]}...")

# 提取token
import json
try:
    data = json.loads(response)
    token = data.get('access_token', '')
    print(f"Token: {token[:50]}..." if token else "未获取到token")
except:
    token = ''
    print("解析响应失败")

# 4. 测试转码状态API
print("\n4. 测试转码状态API...")
if token:
    status_cmd = f'''ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "curl -s http://localhost:8000/api/admin/transcode/status -H 'Authorization: Bearer {token}'"'''
    stdin, stdout, stderr = ssh.exec_command(status_cmd, timeout=30)
    response = stdout.read().decode()
    print(f"状态响应: {response[:500]}...")
else:
    print("跳过（无token）")

# 5. 测试转码日志API
print("\n5. 测试转码日志API...")
if token:
    logs_cmd = f'''ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "curl -s 'http://localhost:8000/api/admin/transcode/logs?lines=5' -H 'Authorization: Bearer {token}'"'''
    stdin, stdout, stderr = ssh.exec_command(logs_cmd, timeout=30)
    response = stdout.read().decode()
    print(f"日志响应: {response[:500]}...")

# 6. 检查转码服务器状态API是否仍在运行
print("\n6. 检查转码服务器状态API...")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port = stdout.read().decode('gbk', errors='ignore')
print(f"端口5001: {port}" if port else "端口5001未监听")

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
print(f"健康检查: {stdout.read().decode()}")

ssh.close()
print("\n验证完成")
