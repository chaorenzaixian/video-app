"""等待服务启动并测试"""
import paramiko
import time
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 等待服务启动
print('等待服务启动...')
for i in range(10):
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/system')
    result = stdout.read().decode()
    if result:
        print(f'服务已启动')
        break
    time.sleep(2)
    print(f'等待中... {i+1}')

# 测试history API
print('\n测试 /api/history...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
result = stdout.read().decode()
print(f'响应: {result[:500]}')

try:
    data = json.loads(result)
    if isinstance(data, dict):
        items = data.get('items', [])
        stats = data.get('stats', {})
        print(f'\nitems数量: {len(items)}')
        print(f'stats: {stats}')
        if items:
            print('\n前3条:')
            for item in items[:3]:
                print(f"  - {item.get('title', '')[:40]}")
except Exception as e:
    print(f'解析失败: {e}')

ssh.close()
