"""
清理pending任务
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建清理脚本
    script = '''import sqlite3
conn = sqlite3.connect('D:/VideoTranscode/data/transcode.db')
c = conn.cursor()
c.execute('SELECT id, filename FROM tasks WHERE status = "pending"')
tasks = c.fetchall()
print(f'Found {len(tasks)} pending tasks')
for t in tasks:
    print(f'  Task {t[0]}: {t[1]}')
c.execute('DELETE FROM tasks WHERE status = "pending"')
conn.commit()
print(f'Deleted {c.rowcount} tasks')
conn.close()
'''
    
    with sftp.file('D:/VideoTranscode/service/clear_pending.py', 'w') as f:
        f.write(script)
    
    sftp.close()
    
    # 执行
    print("执行清理...")
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python clear_pending.py')
    time.sleep(3)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(f"输出: {out}")
    if err:
        print(f"错误: {err}")
    
    # 删除脚本
    client.exec_command('del D:\\VideoTranscode\\service\\clear_pending.py')
    
    # 验证
    print("\n验证:")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/queue')
    result = stdout.read().decode('utf-8', errors='ignore')
    import json
    data = json.loads(result) if result else {}
    print(f"队列任务数: {len(data.get('tasks', []))}")
    
    client.close()

if __name__ == '__main__':
    main()
