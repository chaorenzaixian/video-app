"""检查任务目录结构"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 检查任务目录结构 ===')

# 列出processing目录下的所有任务
stdin, stdout, stderr = ssh.exec_command('dir /b D:\\VideoTranscode\\processing')
tasks = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
print(f'任务数: {len(tasks)}')

# 检查前3个任务的目录结构
for task_id in tasks[:3]:
    task_id = task_id.strip()
    if not task_id:
        continue
    print(f'\n--- 任务: {task_id} ---')
    stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{task_id}"')
    files = stdout.read().decode('utf-8', errors='ignore')
    print(files)
    
    # 检查covers目录
    stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{task_id}\\covers" 2>nul')
    covers = stdout.read().decode('utf-8', errors='ignore')
    if covers.strip():
        print(f'封面文件: {covers.strip().split(chr(10))[:5]}')
    else:
        print('封面目录为空或不存在!')
    
    # 检查hls目录
    stdin, stdout, stderr = ssh.exec_command(f'dir /b "D:\\VideoTranscode\\processing\\{task_id}\\hls" 2>nul')
    hls = stdout.read().decode('utf-8', errors='ignore')
    if hls.strip():
        print(f'HLS文件: {hls.strip().split(chr(10))[:5]}')
    else:
        print('HLS目录为空或不存在!')

ssh.close()
