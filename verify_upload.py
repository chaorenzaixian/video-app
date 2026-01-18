#!/usr/bin/env python3
"""验证上传完整性"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('📊 验证上传完整性')
print('=' * 60)

# 检查 720p
print('\n720p 文件:')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/hls/test_long/720p/ | wc -l"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
count = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  文件数: {count}')

# 检查 480p
print('\n480p 文件:')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/hls/test_long/480p/ | wc -l"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
count = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  文件数: {count}')

# 检查 360p
print('\n360p 文件:')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/hls/test_long/360p/ | wc -l"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
count = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  文件数: {count}')

# 检查 master.m3u8
print('\nmaster.m3u8:')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cat /www/wwwroot/video-app/backend/uploads/hls/test_long/master.m3u8"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(content)

# 检查 720p playlist
print('\n720p playlist.m3u8:')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "head -20 /www/wwwroot/video-app/backend/uploads/hls/test_long/720p/playlist.m3u8"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(content)

ssh.close()
print('\n✅ 上传验证完成!')
