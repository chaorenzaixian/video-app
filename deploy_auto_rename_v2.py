#!/usr/bin/env python3
"""部署自动重命名功能到主服务器 (使用SFTP)"""
import paramiko
import tempfile
import os

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

# 读取本地修改后的文件
with open('backend/app/api/admin_video_ops.py', 'r', encoding='utf-8') as f:
    content = f.read()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("部署自动重命名功能...")

# 1. 先上传到转码服务器
print("\n1. 上传文件到转码服务器...")
sftp = ssh.open_sftp()
temp_path = 'D:/VideoTranscode/temp_admin_video_ops.py'
with sftp.file(temp_path, 'w') as f:
    f.write(content)
sftp.close()
print("   上传完成")

# 2. 从转码服务器 SCP 到主服务器
print("\n2. 传输到主服务器...")
cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no "{temp_path}" root@{MAIN_HOST}:/www/wwwroot/video-app/backend/app/api/admin_video_ops.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
error = stderr.read().decode('utf-8', errors='replace')
if 'denied' in error.lower() or 'error' in error.lower():
    print(f"   错误: {error}")
else:
    print("   传输完成")

# 3. 验证文件
print("\n3. 验证文件...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "grep -c \'get_unique_title\' /www/wwwroot/video-app/backend/app/api/admin_video_ops.py"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
if output and output.isdigit() and int(output) > 0:
    print(f"   ✓ 找到 get_unique_title 函数 ({output} 处)")
else:
    print(f"   ✗ 未找到 get_unique_title 函数 (output: {output})")

# 4. 重启后端服务
print("\n4. 重启后端服务...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "systemctl restart video-app-backend"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()
print("   服务已重启")

# 5. 检查服务状态
print("\n5. 检查服务状态...")
import time
time.sleep(3)
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "systemctl is-active video-app-backend"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
status = stdout.read().decode('utf-8', errors='replace').strip()
if status == 'active':
    print(f"   ✓ 服务状态: {status}")
else:
    print(f"   ✗ 服务状态: {status}")
    # 查看错误日志
    cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "journalctl -u video-app-backend -n 20 --no-pager"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    logs = stdout.read().decode('utf-8', errors='replace')
    print(f"   日志:\n{logs}")

# 清理临时文件
sftp = ssh.open_sftp()
try:
    sftp.remove(temp_path)
except:
    pass
sftp.close()

ssh.close()
print("\n" + "=" * 50)
print("部署完成！同名视频现在会自动重命名为 '视频名 (2)'")
print("=" * 50)
