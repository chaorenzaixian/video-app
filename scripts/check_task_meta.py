import paramiko
import json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 列出processing目录
stdin, stdout, stderr = ssh.exec_command('dir /b D:\\VideoTranscode\\processing')
dirs = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
print(f'Processing dirs: {len(dirs)}')

# 检查第一个目录的task_meta.json
if dirs:
    first_dir = dirs[0].strip()
    print(f'\nChecking: {first_dir}')
    stdin, stdout, stderr = ssh.exec_command(f'type D:\\VideoTranscode\\processing\\{first_dir}\\task_meta.json')
    meta = stdout.read().decode('utf-8', errors='ignore')
    print(f'task_meta.json: {meta}')
    
    # 检查目录内容
    stdin, stdout, stderr = ssh.exec_command(f'dir D:\\VideoTranscode\\processing\\{first_dir}')
    print(f'Dir contents: {stdout.read().decode("gbk", errors="ignore")}')

ssh.close()
