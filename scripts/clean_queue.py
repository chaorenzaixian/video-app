"""
清理无效的队列任务
"""
import paramiko
import json

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 直接操作数据库删除pending任务
    print("清理队列中的pending任务...")
    cmd = '''cd /d D:\\VideoTranscode\\service && python -c "
from task_queue import TaskQueue
q = TaskQueue()
# 获取所有pending任务
import sqlite3
conn = sqlite3.connect('D:/VideoTranscode/data/transcode.db')
c = conn.cursor()
c.execute('SELECT id, filename FROM tasks WHERE status = \"pending\"')
tasks = c.fetchall()
print(f'Found {len(tasks)} pending tasks')
for t in tasks:
    print(f'  Deleting task {t[0]}: {t[1]}')
c.execute('DELETE FROM tasks WHERE status = \"pending\"')
conn.commit()
conn.close()
print('Done')
"'''
    stdin, stdout, stderr = client.exec_command(cmd)
    import time
    time.sleep(3)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(f"输出: {out}")
    if err:
        print(f"错误: {err}")
    
    # 验证
    print("\n验证队列:")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/queue')
    result = stdout.read().decode('utf-8', errors='ignore')
    data = json.loads(result) if result else {}
    print(f"队列任务数: {len(data.get('tasks', []))}")
    
    client.close()

if __name__ == '__main__':
    main()
