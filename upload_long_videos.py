#!/usr/bin/env python3
"""上传长视频到主服务器"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('📤 上传长视频到主服务器')
print('=' * 60)

# 获取长视频列表
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\long\\*.mp4 /b 2>nul', timeout=30)
files = stdout.read().decode('gbk', errors='ignore').strip()

if not files:
    print('❌ 没有长视频需要上传')
else:
    file_list = [f.strip() for f in files.split('\n') if f.strip()]
    print(f'找到 {len(file_list)} 个长视频')
    
    for i, filename in enumerate(file_list):
        print(f'\n[{i+1}/{len(file_list)}] {filename}')
        
        # 获取文件大小
        stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\long\\{filename}\').Length / 1MB"', timeout=30)
        size = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f'  大小: {size} MB')
        
        # 上传
        local_file = f'D:\\VideoTranscode\\completed\\long\\{filename}'
        remote_path = '/www/wwwroot/video-app/backend/uploads/videos/'
        
        scp_cmd = f'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "{local_file}" root@38.47.218.137:{remote_path}'
        
        print('  上传中...')
        start_time = time.time()
        
        stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=600)
        stdout.read()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        
        elapsed = time.time() - start_time
        
        # 验证
        stdin, stdout, stderr = ssh.exec_command(f'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la \'{remote_path}{filename}\' 2>/dev/null"', timeout=30)
        verify = stdout.read().decode('utf-8', errors='ignore').strip()
        
        if filename in verify:
            print(f'  ✅ 成功 ({elapsed:.1f}秒)')
        else:
            print(f'  ❌ 失败')
            if error:
                print(f'  错误: {error[:100]}')

# 清理 processing 目录中的源文件
print('\n🧹 清理 processing 目录...')
stdin, stdout, stderr = ssh.exec_command('del /q D:\\VideoTranscode\\processing\\*.mp4 2>nul', timeout=30)
stdout.read()
print('  ✅ 已清理')

# 最终统计
print('\n📊 主服务器文件统计:')
stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | wc -l"', timeout=30)
count = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  shorts 目录: {count} 个文件')

stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/videos/*.mp4 2>/dev/null | wc -l"', timeout=30)
count = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  videos 目录: {count} 个文件')

ssh.close()
print('\n✅ 完成')
