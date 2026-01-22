"""检查发布历史数据库"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建检查脚本
script = '''
import sqlite3
import os

db_path = r"D:\\VideoTranscode\\data\\transcode.db"
print(f"数据库路径: {db_path}")
print(f"存在: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("数据库不存在!")
    exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 检查表
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"\\n表: {tables}")

# 检查publish_history表
if 'publish_history' in tables:
    cursor = conn.execute("SELECT COUNT(*) FROM publish_history")
    count = cursor.fetchone()[0]
    print(f"\\npublish_history记录数: {count}")
    
    if count > 0:
        cursor = conn.execute("SELECT * FROM publish_history ORDER BY published_at DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - ID:{row['id']}, title:{row['title']}, video_id:{row['video_id']}, published_at:{row['published_at']}")
else:
    print("publish_history表不存在!")

conn.close()
'''

sftp = ssh.open_sftp()
with sftp.file('D:/check_db.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python D:\\check_db.py')
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
