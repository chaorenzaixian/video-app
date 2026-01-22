"""检查待发布的暗网视频"""
import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 获取pending列表
stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
pending = json.loads(stdout.read().decode('utf-8'))

print(f"Total pending: {len(pending.get('items', []))}")
print()

for item in pending.get('items', []):
    task_id = item['task_id']
    is_darkweb = item.get('is_darkweb', False)
    filename = item.get('filename', '')[:40]
    print(f"  {task_id}: darkweb={is_darkweb}, file={filename}")

client.close()
