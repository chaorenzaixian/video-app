#!/usr/bin/env python3
"""部署修复后的封面 API"""
import paramiko
import os

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

# 读取本地修改后的文件
with open('backend/app/api/admin_video_ops.py', 'r', encoding='utf-8') as f:
    content = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("部署修复后的封面 API...")

# 先备份
cmd = r'ssh -i C:\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cp /www/wwwroot/video-app/backend/app/api/admin_video_ops.py /www/wwwroot/video-app/backend/app/api/admin_video_ops.py.bak"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()
print("✓ 已备份原文件")

# 使用 SFTP 通过跳板机上传
# 先上传到转码服务器，再 scp 到主服务器
sftp = ssh.open_sftp()
with sftp.file('D:/temp_admin_video_ops.py', 'w') as f:
    f.write(content)
sftp.close()
print("✓ 已上传到转码服务器")

# 从转码服务器 scp 到主服务器
cmd = r'scp -i C:\server_key -o StrictHostKeyChecking=no D:\temp_admin_video_ops.py root@38.47.218.137:/www/wwwroot/video-app/backend/app/api/admin_video_ops.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
err = stderr.read().decode('utf-8', errors='replace')
if 'error' in err.lower() or 'denied' in err.lower():
    print(f"✗ SCP 错误: {err}")
else:
    print("✓ 已部署到主服务器")

# 重启后端服务
cmd = r'ssh -i C:\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl restart video-app-backend"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()
print("✓ 后端服务已重启")

# 清理临时文件
cmd = 'del D:\\temp_admin_video_ops.py'
ssh.exec_command(cmd, timeout=10)

ssh.close()
print("\n部署完成！")
print("现在长视频的多封面将从 hls/{name}/covers/ 目录读取")
