"""调试发布历史API"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 直接调用API
print('=== 调用 /api/history ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
result = stdout.read().decode('utf-8', errors='ignore')
print(f'原始响应: {result[:500]}')

try:
    data = json.loads(result)
    print(f'\n解析结果:')
    print(f'  类型: {type(data)}')
    if isinstance(data, dict):
        print(f'  键: {data.keys()}')
        print(f'  items: {len(data.get("items", []))}')
        print(f'  stats: {data.get("stats")}')
    elif isinstance(data, list):
        print(f'  列表长度: {len(data)}')
except Exception as e:
    print(f'解析失败: {e}')

# 直接查询数据库
print('\n=== 直接查询数据库 ===')
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')
from task_queue import TaskQueue

queue = TaskQueue()
history = queue.get_publish_history(limit=5, offset=0)
print(f"get_publish_history返回: {len(history)} 条")
for h in history[:3]:
    print(f"  - {h.get('title', '')[:30]}, video_id={h.get('video_id')}")

stats = queue.get_history_stats()
print(f"\\nget_history_stats返回: {stats}")
'''

sftp = ssh.open_sftp()
with sftp.file('D:/debug_hist.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python D:\\debug_hist.py')
print(stdout.read().decode('utf-8', errors='ignore'))
err = stderr.read().decode('utf-8', errors='ignore')
if err:
    print(f'错误: {err}')

ssh.close()
