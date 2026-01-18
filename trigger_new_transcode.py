#!/usr/bin/env python3
"""触发新的转码测试 - 复制一个视频到input目录"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 创建input目录（如果不存在）
ssh.exec_command('mkdir D:\\VideoTranscode\\input 2>nul')
time.sleep(1)

# 使用一个新的测试文件名
test_name = f"cover_test_{int(time.time())}"

# 从downloads/short目录找一个视频复制到input
stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\downloads\\short\\*.mp4" 2>nul')
files = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
files = [f for f in files if f.strip()]

if files:
    source_file = files[0].strip()
    print(f'找到源视频: {source_file}')
    
    # 复制到input目录
    cmd = f'copy "D:\\VideoTranscode\\downloads\\short\\{source_file}" "D:\\VideoTranscode\\input\\{test_name}.mp4"'
    print(f'执行: {cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('gbk', errors='ignore'))
    print(stderr.read().decode('gbk', errors='ignore'))
    
    print(f'\n✓ 已复制视频到 input/{test_name}.mp4')
    print('等待watcher处理...')
else:
    print('downloads/short目录没有视频，尝试其他目录...')
    
    # 尝试从completed目录复制
    stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\completed\\short\\*.mp4" 2>nul')
    files = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
    files = [f for f in files if f.strip() and not '_transcoded' in f]
    
    if not files:
        # 使用已转码的文件作为源
        stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\completed\\short\\*.mp4" 2>nul')
        files = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
        files = [f for f in files if f.strip()]
    
    if files:
        source_file = files[0].strip()
        print(f'找到源视频: completed/short/{source_file}')
        
        cmd = f'copy "D:\\VideoTranscode\\completed\\short\\{source_file}" "D:\\VideoTranscode\\input\\{test_name}.mp4"'
        print(f'执行: {cmd}')
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('gbk', errors='ignore'))
        print(stderr.read().decode('gbk', errors='ignore'))
        
        print(f'\n✓ 已复制视频到 input/{test_name}.mp4')
    else:
        print('没有找到可用的测试视频')

ssh.close()
print(f'\n测试视频名称: {test_name}')
