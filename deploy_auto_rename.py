#!/usr/bin/env python3
"""部署自动重命名功能到主服务器"""
import paramiko

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

# 1. 备份原文件
print("\n1. 备份原文件...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "cp /www/wwwroot/video-app/backend/app/api/admin_video_ops.py /www/wwwroot/video-app/backend/app/api/admin_video_ops.py.bak"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()
print("   备份完成")

# 2. 写入新文件
print("\n2. 写入新文件...")
# 转义内容中的特殊字符
escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

# 使用 base64 编码传输
import base64
encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')

cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "echo \'{encoded}\' | base64 -d > /www/wwwroot/video-app/backend/app/api/admin_video_ops.py"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
error = stderr.read().decode('utf-8', errors='replace')
if error:
    print(f"   错误: {error}")
else:
    print("   写入完成")

# 3. 验证文件
print("\n3. 验证文件...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "grep -c \'get_unique_title\' /www/wwwroot/video-app/backend/app/api/admin_video_ops.py"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8').strip()
if output and int(output) > 0:
    print(f"   ✓ 找到 get_unique_title 函数 ({output} 处)")
else:
    print("   ✗ 未找到 get_unique_title 函数")

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
status = stdout.read().decode('utf-8').strip()
if status == 'active':
    print(f"   ✓ 服务状态: {status}")
else:
    print(f"   ✗ 服务状态: {status}")

ssh.close()
print("\n" + "=" * 50)
print("部署完成！同名视频现在会自动重命名为 '视频名 (2)'")
print("=" * 50)
