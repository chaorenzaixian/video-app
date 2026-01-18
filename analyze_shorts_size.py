#!/usr/bin/env python3
"""分析短视频文件大小"""
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

print("分析短视频文件...")
print("=" * 60)

# 获取所有短视频文件信息
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -lhS /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print("短视频文件（按大小排序）:")
print(stdout.read().decode('utf-8', errors='replace'))

# 检查视频编码信息
print("\n检查最大视频的编码信息:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -S /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | head -1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
largest = stdout.read().decode('utf-8', errors='replace').strip()
if largest:
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffprobe -v quiet -print_format json -show_format -show_streams \\"{largest}\\" 2>/dev/null | head -50"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    print(stdout.read().decode('utf-8', errors='replace'))

# 计算总大小
print("\n短视频总大小:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "du -sh /www/wwwroot/video-app/backend/uploads/shorts/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='replace'))

# 建议
print("\n" + "=" * 60)
print("性能分析结论:")
print("=" * 60)
print("""
问题: 服务器带宽只有 ~7 Mbps，视频加载慢

解决方案:
1. ✅ 已优化 Nginx 配置（启用缓存、断点续传）
2. 建议: 升级服务器带宽（推荐 50-100 Mbps）
3. 建议: 使用 CDN 加速视频分发
4. 建议: 短视频压缩到更小的码率（如 1-2 Mbps）

当前带宽下的预估加载时间:
- 5MB 视频: ~6 秒
- 10MB 视频: ~12 秒
- 40MB 视频: ~45 秒
""")

ssh.close()
