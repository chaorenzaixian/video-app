#!/usr/bin/env python3
"""清理重复视频记录"""
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

print("清理重复视频记录...")
print("=" * 60)

# 找出重复的 hls_url，保留最早的记录
# 删除 ID: 121 (和长腿女神...2 的重复)
# 删除 ID: 122, 123 (极品白虎少萝...的重复)
# 删除 ID: 125 (极品身材JK...的重复)

# 先检查要删除的记录
print("要删除的重复记录:")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT id, title FROM videos WHERE id IN (121, 122, 123, 125);\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

# 删除重复记录
print("\n删除重复记录...")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"DELETE FROM videos WHERE id IN (121, 122, 123, 125);\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

# 验证结果
print("\n剩余的待处理视频:")
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\"SELECT id, title FROM videos WHERE status = 'REVIEWING' ORDER BY id;\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

ssh.close()
print("\n完成!")
