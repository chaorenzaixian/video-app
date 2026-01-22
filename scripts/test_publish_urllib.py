"""使用urllib测试发布"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import urllib.request
import json

# 获取待发布任务
with urllib.request.urlopen('http://localhost:8080/api/pending') as r:
    pending = json.loads(r.read().decode())
print(f"待发布任务数: {len(pending)}")

if not pending:
    print("没有待发布任务")
    exit()

task = pending[0]
task_id = task.get('task_id')
print(f"任务ID: {task_id}")
print(f"文件名: {task.get('filename')}")

# 发布数据
publish_data = {
    "task_id": task_id,
    "title": task.get('name', 'Test'),
    "description": "",
    "selected_cover": task.get('best_cover', 5),
    "is_vip_only": False,
    "is_featured": False,
    "coin_price": 0,
    "free_preview_seconds": 15
}

print(f"\\n发布数据: {json.dumps(publish_data, ensure_ascii=False)}")

# 发送发布请求
print("\\n发送发布请求...")
try:
    req = urllib.request.Request(
        'http://localhost:8080/api/publish',
        data=json.dumps(publish_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        result = json.loads(r.read().decode())
        print(f"响应: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP错误: {e.code}")
    print(f"响应: {e.read().decode()}")
except Exception as e:
    print(f"请求失败: {e}")
    import traceback
    traceback.print_exc()

# 检查发布历史
print("\\n检查发布历史...")
with urllib.request.urlopen('http://localhost:8080/api/history') as r:
    history = json.loads(r.read().decode())
items = history.get('items', []) if isinstance(history, dict) else history
print(f"发布历史数: {len(items)}")
'''

# 上传并执行
sftp = ssh.open_sftp()
with sftp.file('D:/test_pub2.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\test_pub2.py', timeout=360)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
