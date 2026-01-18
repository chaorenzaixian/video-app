#!/usr/bin/env python3
"""启动并测试转码状态API"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("✓ 已连接")

# 1. 检查status_api.py是否存在
print("\n1. 检查文件...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\status_api.py')
print(stdout.read().decode('gbk', errors='ignore'))

# 2. 杀死可能占用端口的进程
print("\n2. 清理旧进程...")
ssh.exec_command('taskkill /f /im python.exe')
time.sleep(2)

# 3. 后台启动API
print("\n3. 启动API...")
# 使用start命令在后台启动
start_cmd = 'start /b python D:\\VideoTranscode\\status_api.py > D:\\VideoTranscode\\logs\\api.log 2>&1'
stdin, stdout, stderr = ssh.exec_command(f'cmd /c "{start_cmd}"')
time.sleep(3)

# 4. 检查端口
print("\n4. 检查端口5001...")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port_info = stdout.read().decode('gbk', errors='ignore')
print(port_info if port_info else "端口5001未监听")

# 5. 检查Python进程
print("\n5. Python进程:")
stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
print(stdout.read().decode('gbk', errors='ignore'))

# 6. 测试健康检查
print("\n6. 测试API...")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
response = stdout.read().decode()
print(f"响应: {response}")

# 7. 如果失败，查看日志
if 'ok' not in response:
    print("\n7. 查看API日志...")
    stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\logs\\api.log')
    log = stdout.read().decode('gbk', errors='ignore')
    print(log[:1000] if log else "无日志")

ssh.close()
print("\n完成")
