#!/usr/bin/env python3
"""移动测试视频到正确的目录"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

test_name = "cover_test_1768652638"

# 确保downloads/short目录存在
ssh.exec_command('mkdir "D:\\VideoTranscode\\downloads\\short" 2>nul')
time.sleep(1)

# 移动视频到downloads/short目录
cmd = f'move "D:\\VideoTranscode\\input\\{test_name}.mp4" "D:\\VideoTranscode\\downloads\\short\\{test_name}.mp4"'
print(f'执行: {cmd}')
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('gbk', errors='ignore'))
print(stderr.read().decode('gbk', errors='ignore'))

# 确认文件已移动
stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\downloads\\short"')
print('\ndownloads/short目录:')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
print(f'\n✓ 视频已移动到 downloads/short/{test_name}.mp4')
print('等待watcher处理...')
