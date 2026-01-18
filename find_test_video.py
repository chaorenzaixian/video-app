#!/usr/bin/env python3
"""查找可用的测试视频"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查downloads和completed目录
dirs = [
    'D:\\VideoTranscode\\downloads',
    'D:\\VideoTranscode\\completed',
    'D:\\VideoTranscode\\processing',
]

for d in dirs:
    stdin, stdout, stderr = ssh.exec_command(f'dir "{d}" /b 2>nul')
    out = stdout.read().decode('gbk', errors='ignore').strip()
    print(f'{d}:')
    if out:
        for line in out.split('\n')[:10]:  # 只显示前10个
            print(f'  {line}')
    else:
        print('  (空)')
    print()

# 查找mp4文件
print('查找所有mp4文件:')
stdin, stdout, stderr = ssh.exec_command('dir /s /b D:\\VideoTranscode\\*.mp4 2>nul')
out = stdout.read().decode('gbk', errors='ignore').strip()
if out:
    for line in out.split('\n')[:10]:
        print(f'  {line}')
else:
    print('  没有找到mp4文件')

ssh.close()
