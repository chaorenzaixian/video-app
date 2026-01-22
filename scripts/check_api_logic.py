import paramiko
import json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 检查API逻辑 ===')

# /api/queue - 应该返回正在转码的任务
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/queue')
data = json.loads(stdout.read().decode())
print(f'/api/queue (转码中): {len(data)} items')
if data:
    for t in data[:3]:
        fname = t.get('filename', '')[:30]
        status = t.get('status')
        print(f'  - {fname}... status={status}')

# /api/pending - 应该返回ready状态的任务
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
data = json.loads(stdout.read().decode())
print(f'/api/pending (待发布): {len(data)} items')
if data:
    for t in data[:3]:
        fname = t.get('filename', '')[:30]
        status = t.get('status')
        print(f'  - {fname}... status={status}')

# /api/history - 发布历史
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
data = json.loads(stdout.read().decode())
print(f'/api/history (发布历史): {len(data)} items')

ssh.close()
