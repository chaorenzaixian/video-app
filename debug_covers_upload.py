#!/usr/bin/env python3
"""调试封面上传问题"""
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

print("调试封面上传问题...")
print("=" * 60)

# 1. 检查转码服务器上的输出目录
print("\n1. 检查转码服务器上的输出目录:")
cmd = 'dir /b "D:\\VideoTranscode\\output"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(f"输出目录列表:\n{output}")

# 2. 检查最新的输出目录是否有 covers
videos = output.split('\n') if output else []
for video in videos[-3:]:  # 检查最新3个
    if not video.strip():
        continue
    video = video.strip()
    print(f"\n检查 {video}:")
    
    # 检查 covers 目录
    cmd = f'dir /b "D:\\VideoTranscode\\output\\{video}\\covers" 2>nul'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    covers = stdout.read().decode('utf-8', errors='replace').strip()
    if covers:
        print(f"  covers 目录内容: {covers}")
    else:
        print(f"  covers 目录: 不存在或为空")
    
    # 检查主封面
    cmd = f'dir "D:\\VideoTranscode\\output\\{video}\\*.webp" 2>nul'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    webp = stdout.read().decode('utf-8', errors='replace').strip()
    if webp:
        print(f"  主封面: 存在")
    else:
        print(f"  主封面: 不存在")

# 3. 检查 watcher 日志
print("\n\n2. 检查 watcher 日志 (最近的封面相关日志):")
cmd = 'type "D:\\VideoTranscode\\logs\\watcher.log" | findstr /i "cover"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
logs = stdout.read().decode('utf-8', errors='replace').strip()
if logs:
    lines = logs.split('\n')
    for line in lines[-20:]:  # 最近20行
        print(f"  {line}")
else:
    print("  没有找到封面相关日志")

# 4. 检查 watcher 脚本中的封面上传部分
print("\n\n3. 检查 watcher 脚本中的封面上传代码:")
sftp = ssh.open_sftp()
with sftp.file('D:/VideoTranscode/scripts/watcher.ps1', 'r') as f:
    content = f.read().decode('utf-8')
sftp.close()

# 找到封面上传部分
lines = content.split('\n')
in_cover_section = False
cover_lines = []
for i, line in enumerate(lines):
    if 'Uploading covers' in line:
        in_cover_section = True
    if in_cover_section:
        cover_lines.append(f"{i+1}: {line}")
        if len(cover_lines) > 15:
            break

if cover_lines:
    print("封面上传代码:")
    for line in cover_lines:
        print(f"  {line}")
else:
    print("  未找到封面上传代码")

# 5. 手动测试封面上传
print("\n\n4. 手动测试封面上传到主服务器:")
# 找一个有 covers 的目录
for video in videos[-3:]:
    if not video.strip():
        continue
    video = video.strip()
    cmd = f'dir /b "D:\\VideoTranscode\\output\\{video}\\covers\\cover_1.webp" 2>nul'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    if stdout.read().decode('utf-8', errors='replace').strip():
        print(f"找到测试文件: {video}/covers/cover_1.webp")
        
        # 尝试手动上传
        print("尝试手动创建远程目录...")
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL root@{MAIN_HOST} "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/{video}/covers"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        err = stderr.read().decode('utf-8', errors='replace')
        if err:
            print(f"  错误: {err}")
        else:
            print("  目录创建成功")
        
        print("尝试上传封面...")
        cmd = f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\VideoTranscode\\output\\{video}\\covers\\cover_1.webp" root@{MAIN_HOST}:/www/wwwroot/video-app/backend/uploads/hls/{video}/covers/'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        err = stderr.read().decode('utf-8', errors='replace')
        out = stdout.read().decode('utf-8', errors='replace')
        if err:
            print(f"  错误: {err}")
        else:
            print(f"  上传成功")
        
        # 验证
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "ls -la /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        result = stdout.read().decode('utf-8', errors='replace')
        print(f"  验证结果: {result}")
        break

ssh.close()
print("\n调试完成")
