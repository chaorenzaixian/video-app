#!/usr/bin/env python3
"""为所有视频生成多封面"""
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

print("为所有视频生成多封面...")
print("=" * 60)

# 获取所有视频目录
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
videos = stdout.read().decode('utf-8', errors='replace').strip().split('\n')

print(f"找到 {len(videos)} 个视频目录")

processed = 0
skipped = 0
for video in videos:
    if not video.strip():
        continue
    video = video.strip()
    
    # 检查是否已有封面
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/*.webp 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    cover_count = stdout.read().decode('utf-8', errors='replace').strip()
    
    if cover_count and int(cover_count) >= 5:
        skipped += 1
        continue
    
    # 检查是否有 master.m3u8
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f /www/wwwroot/video-app/backend/uploads/hls/{video}/master.m3u8 && echo yes || echo no"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    has_master = stdout.read().decode('utf-8', errors='replace').strip()
    
    if has_master != 'yes':
        skipped += 1
        continue
    
    print(f"处理 {video}...", end=" ", flush=True)
    
    # 创建 covers 目录
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/{video}/covers"'
    ssh.exec_command(cmd, timeout=60)
    
    # 找到 ts 文件
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "find /www/wwwroot/video-app/backend/uploads/hls/{video} -name \\"*.ts\\" -type f 2>/dev/null | sort | head -20"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    ts_files = [f.strip() for f in stdout.read().decode('utf-8', errors='replace').strip().split('\n') if f.strip()]
    
    if not ts_files:
        print("跳过(无ts)")
        skipped += 1
        continue
    
    # 生成封面
    generated = 0
    for i in range(1, 11):
        ts_idx = min(i - 1, len(ts_files) - 1)
        ts_file = ts_files[ts_idx]
        cover_path = f'/www/wwwroot/video-app/backend/uploads/hls/{video}/covers/cover_{i}.webp'
        
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -y -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 \\"{cover_path}\\" 2>/dev/null"'
        ssh.exec_command(cmd, timeout=120)
        
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{cover_path}\\" && echo 1 || echo 0"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        if stdout.read().decode('utf-8', errors='replace').strip() == '1':
            generated += 1
    
    print(f"{generated} 个封面")
    processed += 1

print(f"\n完成！处理了 {processed} 个视频，跳过了 {skipped} 个")

# 验证结果
print("\n验证结果:")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "for d in /www/wwwroot/video-app/backend/uploads/hls/*/; do name=$(basename \\"$d\\"); count=$(ls \\"$d/covers/\\"*.webp 2>/dev/null | wc -l); if [ \\"$count\\" -gt 0 ]; then echo \\"$name: $count covers\\"; fi; done | wc -l"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
total = stdout.read().decode('utf-8', errors='replace').strip()
print(f"有封面的视频数量: {total}")

ssh.close()
