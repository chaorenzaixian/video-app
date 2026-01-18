#!/usr/bin/env python3
"""调试封面问题"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('=== 检查最新视频的封面 ===')

# 检查饼饼大王目录
cmd = r'ssh -i C:\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/hls/饼饼大王/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print('饼饼大王 HLS 目录:')
print(output)

# 检查 covers 子目录
cmd = r'ssh -i C:\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/hls/饼饼大王/covers/ 2>&1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print('\ncovers 子目录:')
print(output)

# 测试 API 返回
cmd = r'ssh -i C:\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/v1/admin/videos/114/covers -H \"Authorization: Bearer test\" 2>&1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print('\nAPI 返回:')
print(output[:500])

ssh.close()
