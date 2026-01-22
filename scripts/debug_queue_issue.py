"""调试队列问题"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 直接在远程服务器上执行Python代码来检查pending_publish
print("检查pending_publish中的任务状态分布:")
cmd = '''python -c "
import requests
import json

# 获取所有pending数据
r = requests.get('http://localhost:8080/api/pending', timeout=10)
pending = r.json()
print(f'Pending count: {len(pending)}')

# 统计状态
statuses = {}
for item in pending:
    status = item.get('status', 'unknown')
    statuses[status] = statuses.get(status, 0) + 1
print(f'Status distribution: {statuses}')

# 获取queue数据
r = requests.get('http://localhost:8080/api/queue', timeout=10)
queue = r.json()
print(f'Queue count: {len(queue)}')
for item in queue:
    print(f'  - {item.get(\"filename\")}: {item.get(\"status\")}')
"
'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
