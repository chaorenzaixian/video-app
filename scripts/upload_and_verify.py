"""上传并验证web_ui.py"""
import paramiko
import os

# 读取本地文件
local_path = 'transcode_service/web_ui.py'
with open(local_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'本地文件大小: {len(content)} 字符')
print(f'包含offset: {"offset = (page - 1) * per_page" in content}')
print(f'包含limit=per_page: {"limit=per_page" in content}')

# 连接远程服务器
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 使用SFTP上传
sftp = ssh.open_sftp()
remote_path = 'D:/VideoTranscode/service/web_ui.py'

print(f'\n上传到: {remote_path}')
with sftp.file(remote_path, 'w') as f:
    f.write(content)

# 验证上传
print('\n验证上传...')
with sftp.file(remote_path, 'r') as f:
    remote_content = f.read().decode('utf-8')

print(f'远程文件大小: {len(remote_content)} 字符')
print(f'包含offset: {"offset = (page - 1) * per_page" in remote_content}')
print(f'包含limit=per_page: {"limit=per_page" in remote_content}')

sftp.close()

# 重启服务
print('\n重启服务...')
stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM python.exe 2>nul')
stdout.read()

import time
time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('cd /d D:\\VideoTranscode\\service && start /b python web_ui.py')
stdout.read()

time.sleep(3)

# 测试API
print('\n测试API...')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
result = stdout.read().decode('utf-8', errors='ignore')
print(f'响应: {result[:500]}')

import json
try:
    data = json.loads(result)
    if isinstance(data, dict):
        print(f'\nitems数量: {len(data.get("items", []))}')
        print(f'stats: {data.get("stats")}')
    elif isinstance(data, list):
        print(f'\n列表长度: {len(data)}')
except:
    print('解析失败')

ssh.close()
print('\n完成!')
