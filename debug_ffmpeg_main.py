#!/usr/bin/env python3
"""调试主服务器上的 ffmpeg"""
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

print("调试主服务器上的 ffmpeg...")
print("=" * 60)

# 检查 ffmpeg 是否安装
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "which ffmpeg && ffmpeg -version | head -1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(f"ffmpeg: {output}")
if err:
    print(f"错误: {err}")

# 检查一个具体的视频目录
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -la /www/wwwroot/video-app/backend/uploads/hls/64/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
print(f"\n视频目录 64 内容:\n{output}")

# 找一个 ts 文件
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/64/*.ts | head -1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
ts_file = stdout.read().decode('utf-8', errors='replace').strip()
print(f"\nts 文件: {ts_file}")

if ts_file:
    # 检查 ts 文件信息
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffprobe -v error -show_format -show_streams \\"{ts_file}\\" 2>&1 | head -20"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"\nts 文件信息:\n{output}")
    
    # 尝试生成封面
    print("\n尝试生成封面...")
    cover_path = '/tmp/test_cover.webp'
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -y -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 \\"{cover_path}\\" 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"ffmpeg 输出:\n{output[:1000]}")
    
    # 检查是否生成成功
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -la {cover_path} 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"\n封面文件: {output}")
    
    # 尝试用 jpg 格式
    print("\n尝试生成 jpg 格式...")
    jpg_path = '/tmp/test_cover.jpg'
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -y -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" \\"{jpg_path}\\" 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"ffmpeg 输出:\n{output[:500]}")
    
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -la {jpg_path} 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"jpg 文件: {output}")

ssh.close()
print("\n调试完成")
