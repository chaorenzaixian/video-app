"""检查HLS目录结构"""
import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 获取pending列表
stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
pending = json.loads(stdout.read().decode('utf-8'))

print(f"Pending count: {len(pending.get('items', []))}")

# 检查第一个任务的HLS结构
if pending.get('items'):
    task_id = pending['items'][0]['task_id']
    print(f"\nChecking task: {task_id}")
    
    # 检查HLS目录
    cmd = f'dir /s /b D:\\VideoTranscode\\processing\\{task_id}\\hls'
    stdin, stdout, stderr = client.exec_command(cmd)
    files = stdout.read().decode('gbk', errors='ignore')
    print(f"HLS files:\n{files}")
    
    # 检查master.m3u8
    cmd2 = f'type D:\\VideoTranscode\\processing\\{task_id}\\hls\\master.m3u8'
    stdin, stdout, stderr = client.exec_command(cmd2)
    m3u8 = stdout.read().decode('utf-8', errors='ignore')
    print(f"master.m3u8:\n{m3u8}")

client.close()
