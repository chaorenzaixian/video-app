"""直接在远程测试API"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')

# 直接导入并测试
from task_queue import TaskQueue

print("创建TaskQueue实例...")
queue = TaskQueue()

print("\\n调用get_publish_history...")
history = queue.get_publish_history(limit=20, offset=0)
print(f"返回类型: {type(history)}")
print(f"返回长度: {len(history)}")

if history:
    print("\\n前3条记录:")
    for h in history[:3]:
        print(f"  - {h}")

print("\\n调用get_history_stats...")
stats = queue.get_history_stats()
print(f"返回: {stats}")

# 测试Flask应用
print("\\n\\n=== 测试Flask应用 ===")
from web_ui import app, queue as app_queue

print(f"app_queue是同一个实例吗: {queue is app_queue}")
print(f"app_queue.db_path: {app_queue.db_path}")

# 直接调用get_history函数
with app.test_client() as client:
    print("\\n调用/api/history...")
    response = client.get('/api/history')
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.get_json()}")
'''

sftp = ssh.open_sftp()
with sftp.file('D:/test_api_direct.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\test_api_direct.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
