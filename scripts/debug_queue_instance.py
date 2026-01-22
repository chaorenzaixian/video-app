"""调试queue实例"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')

from web_ui import app, queue
from config import DATABASE_PATH

print(f"DATABASE_PATH: {DATABASE_PATH}")
print(f"queue.db_path: {queue.db_path}")
print(f"相同: {DATABASE_PATH == queue.db_path}")

# 直接查询queue的数据库
print("\\n直接查询queue的数据库...")
history = queue.get_publish_history(limit=5, offset=0)
print(f"返回: {len(history)} 条")
for h in history[:3]:
    print(f"  - {h.get('title', '')[:30]}")

# 检查数据库文件
import os
print(f"\\n数据库文件存在: {os.path.exists(queue.db_path)}")
print(f"数据库文件大小: {os.path.getsize(queue.db_path) if os.path.exists(queue.db_path) else 0} bytes")

# 直接用sqlite3查询
import sqlite3
conn = sqlite3.connect(queue.db_path)
cursor = conn.execute("SELECT COUNT(*) FROM publish_history")
count = cursor.fetchone()[0]
print(f"\\n直接SQL查询publish_history: {count} 条")
conn.close()
'''

sftp = ssh.open_sftp()
with sftp.file('D:/debug_queue.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\debug_queue.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
