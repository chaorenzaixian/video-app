#!/usr/bin/env python3
"""重启 video-app-backend 服务"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('🔄 重启 video-app-backend 服务')
print('=' * 60)

# 重启服务
print('\n1. 重启服务...')
stdin, stdout, stderr = ssh.exec_command(
    'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl restart video-app-backend.service"',
    timeout=60
)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f'  stdout: {out}')
print(f'  stderr: {err}')

# 等待
print('\n⏳ 等待服务启动...')
time.sleep(8)

# 检查状态
print('\n2. 检查服务状态...')
stdin, stdout, stderr = ssh.exec_command(
    'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl status video-app-backend.service | head -20"',
    timeout=30
)
out = stdout.read().decode('utf-8', errors='ignore')
print(out)

# 测试健康检查
print('\n3. 测试健康检查...')
stdin, stdout, stderr = ssh.exec_command(
    'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/health"',
    timeout=30
)
out = stdout.read().decode('utf-8', errors='ignore')
print(f'  {out}')

# 测试新 API
print('\n4. 测试导入 API...')
cmd = '''ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s -X POST -H 'Content-Type: application/json' -H 'X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U' -d '{\\\"filename\\\":\\\"api_test_2\\\",\\\"title\\\":\\\"API Test 2\\\",\\\"is_short\\\":true,\\\"video_url\\\":\\\"/uploads/shorts/api_test.mp4\\\",\\\"cover_url\\\":\\\"/uploads/thumbnails/api_test.webp\\\",\\\"duration\\\":60.0}' http://localhost:8000/api/v1/admin/videos/import-from-transcode"'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f'  {out}')

ssh.close()
print('\n✅ Done!')
