"""检查预览视频文件"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 检查预览视频文件 ===')

# 检查任务目录中的预览视频
task_id = "20260120143014814762"
stdin, stdout, stderr = ssh.exec_command(f'dir "D:\\VideoTranscode\\processing\\{task_id}\\*preview*" 2>nul')
output = stdout.read().decode('gbk', errors='ignore')
print(f'任务 {task_id} 的预览文件:')
print(output if output.strip() else '  无预览文件')

# 检查所有任务的预览文件
print('\n=== 所有任务的预览文件 ===')
stdin, stdout, stderr = ssh.exec_command('dir /s /b "D:\\VideoTranscode\\processing\\*_preview.webm" 2>nul')
output = stdout.read().decode('gbk', errors='ignore')
if output.strip():
    files = output.strip().split('\n')
    print(f'找到 {len(files)} 个预览文件')
    for f in files[:5]:
        print(f'  - {f}')
else:
    print('没有找到预览文件')

# 检查API返回的任务中preview_path
print('\n=== API返回的预览路径 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
import json
data = json.loads(stdout.read().decode())
for task in data[:5]:
    task_id = task.get('task_id')
    preview_path = task.get('preview_path')
    preview_url = task.get('preview_url')
    print(f'{task_id}: preview_path={preview_path}, preview_url={preview_url}')

ssh.close()
