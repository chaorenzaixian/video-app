#!/usr/bin/env python3
"""在主服务器上为视频生成多封面 - 修复版"""
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

print("在主服务器上为视频生成多封面...")
print("=" * 60)

# 检查 ffmpeg
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "which ffmpeg"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
ffmpeg_path = stdout.read().decode('utf-8', errors='replace').strip()
if not ffmpeg_path:
    print("错误: 主服务器上没有安装 ffmpeg")
    print("尝试安装 ffmpeg...")
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "apt-get update && apt-get install -y ffmpeg"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output[-500:])
else:
    print(f"ffmpeg 路径: {ffmpeg_path}")

# 获取所有视频目录
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
videos = stdout.read().decode('utf-8', errors='replace').strip().split('\n')

print(f"找到 {len(videos)} 个视频目录")

processed = 0
for video in videos:
    if not video.strip():
        continue
    video = video.strip()
    
    # 检查是否已有封面
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/*.webp 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    cover_count = stdout.read().decode('utf-8', errors='replace').strip()
    
    if cover_count and int(cover_count) >= 5:
        print(f"跳过 {video}: 已有 {cover_count} 个封面")
        continue
    
    # 检查是否有 master.m3u8
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f /www/wwwroot/video-app/backend/uploads/hls/{video}/master.m3u8 && echo yes || echo no"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    has_master = stdout.read().decode('utf-8', errors='replace').strip()
    
    if has_master != 'yes':
        continue
    
    print(f"\n处理 {video}...")
    
    # 创建 covers 目录
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/{video}/covers"'
    ssh.exec_command(cmd, timeout=60)
    
    # 找到 ts 文件 - 在子目录中查找
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "find /www/wwwroot/video-app/backend/uploads/hls/{video} -name \\"*.ts\\" -type f 2>/dev/null | sort | head -20"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    ts_files = [f.strip() for f in stdout.read().decode('utf-8', errors='replace').strip().split('\n') if f.strip()]
    
    if not ts_files:
        print(f"  跳过: 没有 ts 文件")
        continue
    
    print(f"  找到 {len(ts_files)} 个 ts 文件")
    print(f"  第一个: {ts_files[0]}")
    
    # 从不同的 ts 文件生成封面
    generated = 0
    for i in range(1, 11):
        # 选择不同的 ts 文件
        ts_idx = min(i - 1, len(ts_files) - 1)
        ts_file = ts_files[ts_idx]
        
        cover_path = f'/www/wwwroot/video-app/backend/uploads/hls/{video}/covers/cover_{i}.webp'
        
        # 使用 ffmpeg 生成封面 - 尝试不同的方法
        # 方法1: 直接从 ts 文件提取
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -y -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 \\"{cover_path}\\" 2>&1"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
        output = stdout.read().decode('utf-8', errors='replace')
        
        # 检查是否生成成功
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{cover_path}\\" && stat -c%s \\"{cover_path}\\" || echo 0"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        size = stdout.read().decode('utf-8', errors='replace').strip()
        
        if size and int(size) > 0:
            generated += 1
            if i <= 3:
                print(f"  生成 cover_{i}.webp ({size} bytes)")
        else:
            # 如果 webp 失败，尝试 jpg
            jpg_path = cover_path.replace('.webp', '.jpg')
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -y -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" \\"{jpg_path}\\" 2>&1"'
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            
            # 如果 jpg 成功，转换为 webp
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{jpg_path}\\" && ffmpeg -y -i \\"{jpg_path}\\" -c:v libwebp -quality 85 \\"{cover_path}\\" && rm \\"{jpg_path}\\" 2>&1"'
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{cover_path}\\" && stat -c%s \\"{cover_path}\\" || echo 0"'
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            size = stdout.read().decode('utf-8', errors='replace').strip()
            
            if size and int(size) > 0:
                generated += 1
                if i <= 3:
                    print(f"  生成 cover_{i}.webp (via jpg, {size} bytes)")
    
    print(f"  完成: 生成了 {generated} 个封面")
    processed += 1
    
    # 限制处理数量
    if processed >= 5:
        print("\n已处理 5 个视频，暂停...")
        break

# 验证结果
print("\n\n验证结果...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "for d in /www/wwwroot/video-app/backend/uploads/hls/*/; do name=$(basename \\"$d\\"); count=$(ls \\"$d/covers/\\"*.webp 2>/dev/null | wc -l); if [ \\"$count\\" -gt 0 ]; then echo \\"$name: $count covers\\"; fi; done"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
result = stdout.read().decode('utf-8', errors='replace')
print(result if result else "没有找到任何封面")

ssh.close()
print("\n完成！")
