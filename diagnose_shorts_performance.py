#!/usr/bin/env python3
"""诊断短视频性能问题"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("诊断短视频性能问题...")
print("=" * 60)

# 1. 检查服务器负载
print("\n1. 服务器负载:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "uptime && free -h && df -h /www"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 2. 检查 nginx 状态
print("\n2. Nginx 状态:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "systemctl status nginx | head -10"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 3. 检查短视频文件大小
print("\n3. 短视频文件大小:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -lh /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | head -10"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 4. 测试短视频 API 响应时间
print("\n4. 短视频 API 响应时间:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "time curl -s -o /dev/null -w \'%{{time_total}}s\' \'http://localhost:8000/api/v1/videos/shorts?page=1&page_size=10\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"API 响应时间: {output}")

# 5. 检查数据库查询
print("\n5. 短视频数量:")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT COUNT(*) FROM videos WHERE is_short = true AND status = 'PUBLISHED';\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 6. 检查 nginx 配置中的缓存设置
print("\n6. Nginx 缓存配置:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "grep -A5 \'location.*uploads\' /www/server/panel/vhost/nginx/*.conf 2>/dev/null | head -20"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 7. 测试视频文件下载速度
print("\n7. 测试视频文件下载速度:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | head -1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
first_video = stdout.read().decode('utf-8', errors='replace').strip()
if first_video:
    video_name = first_video.split('/')[-1]
    print(f"测试文件: {video_name}")
    # 本地下载测试
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "curl -s -o /dev/null -w \'下载速度: %{{speed_download}} bytes/s, 总时间: %{{time_total}}s\' \'http://localhost/uploads/shorts/{video_name}\'"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("\n诊断完成!")
