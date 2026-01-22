"""查找有封面的任务"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 查找有封面的任务 ===')

# 列出所有任务
stdin, stdout, stderr = ssh.exec_command('dir /b D:\\VideoTranscode\\processing')
tasks = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')

tasks_with_covers = []
tasks_without_covers = []

for task_id in tasks:
    task_id = task_id.strip()
    if not task_id:
        continue
    
    # 检查covers目录是否存在且有文件
    stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{task_id}\\covers\\*.webp" 2>nul')
    covers = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if covers:
        tasks_with_covers.append(task_id)
    else:
        tasks_without_covers.append(task_id)

print(f'有封面的任务: {len(tasks_with_covers)}')
for t in tasks_with_covers[:5]:
    print(f'  - {t}')

print(f'\n没有封面的任务: {len(tasks_without_covers)}')
for t in tasks_without_covers[:5]:
    print(f'  - {t}')

# 检查pending_publish中的任务
print('\n=== 检查API返回的待发布任务 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
import json
data = json.loads(stdout.read().decode())
print(f'API返回任务数: {len(data)}')

for task in data[:3]:
    task_id = task.get('task_id')
    covers = task.get('covers', [])
    covers_dir = task.get('covers_dir', '')
    print(f'\n任务: {task_id}')
    print(f'  covers_dir: {covers_dir}')
    print(f'  covers数量: {len(covers)}')
    if covers:
        print(f'  第一个封面: {covers[0].get("url")}')

ssh.close()
