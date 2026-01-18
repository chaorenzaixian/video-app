#!/usr/bin/env python3
"""列出已上传的视频"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('📊 已上传的视频')
print('=' * 60)

# 获取短视频
print('\n📁 短视频:')
stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null"', timeout=60)
shorts = stdout.read().decode('utf-8', errors='ignore').strip()
if shorts:
    for path in shorts.split('\n'):
        name = path.split('/')[-1].replace('.mp4', '')
        print(f'  - {name}')
        print(f'    视频: /uploads/shorts/{name}.mp4')
        print(f'    封面: /uploads/thumbnails/{name}.webp')
else:
    print('  (无)')

# 获取长视频 HLS
print('\n📁 长视频 (HLS):')
stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -d /www/wwwroot/video-app/backend/uploads/hls/*/ 2>/dev/null"', timeout=60)
hls = stdout.read().decode('utf-8', errors='ignore').strip()
if hls:
    for path in hls.split('\n'):
        name = path.rstrip('/').split('/')[-1]
        print(f'  - {name}')
        print(f'    HLS: /uploads/hls/{name}/master.m3u8')
        print(f'    封面: /uploads/thumbnails/{name}.webp')
        print(f'    预览: /uploads/previews/{name}_preview.webm')
else:
    print('  (无)')

ssh.close()

print('\n' + '=' * 60)
print('要导入这些视频到数据库，需要在主服务器上重启后端服务')
print('或者直接在数据库中插入记录')
