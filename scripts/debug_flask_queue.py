"""调试Flask中的queue"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')

# 模拟Flask应用启动
print("导入web_ui模块...")
import web_ui

print(f"\\nqueue实例: {web_ui.queue}")
print(f"queue.db_path: {web_ui.queue.db_path}")

# 直接调用queue的方法
print("\\n调用queue.get_publish_history(limit=20, offset=0)...")
result = web_ui.queue.get_publish_history(limit=20, offset=0)
print(f"返回类型: {type(result)}")
print(f"返回长度: {len(result)}")

if result:
    print("\\n前3条:")
    for r in result[:3]:
        print(f"  - {r.get('title', '')[:30]}")
else:
    print("返回空列表!")
    
    # 检查数据库连接
    print("\\n检查数据库连接...")
    import sqlite3
    conn = sqlite3.connect(web_ui.queue.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM publish_history ORDER BY published_at DESC LIMIT 5")
    rows = cursor.fetchall()
    print(f"直接SQL查询: {len(rows)} 条")
    for row in rows:
        print(f"  - {dict(row).get('title', '')[:30]}")
    conn.close()

# 测试Flask test_client
print("\\n\\n=== 使用Flask test_client ===")
with web_ui.app.test_client() as client:
    response = client.get('/api/history')
    print(f"状态码: {response.status_code}")
    data = response.get_json()
    print(f"响应类型: {type(data)}")
    if isinstance(data, dict):
        print(f"items: {len(data.get('items', []))}")
        print(f"stats: {data.get('stats')}")
    elif isinstance(data, list):
        print(f"列表长度: {len(data)}")
'''

sftp = ssh.open_sftp()
with sftp.file('D:/debug_flask.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\debug_flask.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
