#!/usr/bin/env python3
"""清理测试短视频文件"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("清理测试短视频文件...")
print("=" * 60)

# 查看数据库中的短视频记录
print("\n1. 数据库中的短视频记录:")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT id, title, hls_url FROM videos WHERE is_short = true AND status = 'PUBLISHED';\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 识别测试文件（文件名包含 test, luoli_, video_short 等）
print("\n2. 识别测试文件:")
test_patterns = [
    '*test*.mp4',
    '*luoli_*.mp4', 
    '*video_short_*.mp4',
    '*_transcoded.mp4',
    '*workflow*.mp4',
    '*admin_test*.mp4',
    '*new_test*.mp4',
    '*multi_cover*.mp4'
]

for pattern in test_patterns:
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -lh /www/wwwroot/video-app/backend/uploads/shorts/{pattern} 2>/dev/null"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='replace').strip()
    if output:
        print(output)

# 删除测试文件
print("\n3. 删除测试文件...")
for pattern in test_patterns:
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "rm -f /www/wwwroot/video-app/backend/uploads/shorts/{pattern}"'
    ssh.exec_command(cmd, timeout=60)

# 删除空文件
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "find /www/wwwroot/video-app/backend/uploads/shorts/ -size 0 -delete"'
ssh.exec_command(cmd, timeout=60)

# 验证剩余文件
print("\n4. 剩余的短视频文件:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -lhS /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 新的总大小
print("\n5. 清理后的总大小:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "du -sh /www/wwwroot/video-app/backend/uploads/shorts/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("\n完成!")
