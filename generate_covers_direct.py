#!/usr/bin/env python3
"""直接在主服务器上为视频生成多封面"""
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
        print(f"跳过 {video}: 没有 master.m3u8")
        continue
    
    print(f"\n处理 {video}...")
    
    # 创建 covers 目录
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/{video}/covers"'
    ssh.exec_command(cmd, timeout=60)
    
    # 找到 ts 文件
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "find /www/wwwroot/video-app/backend/uploads/hls/{video} -name \\"*.ts\\" -type f | sort | head -20"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    ts_files = stdout.read().decode('utf-8', errors='replace').strip().split('\n')
    
    if not ts_files or not ts_files[0]:
        print(f"  跳过: 没有 ts 文件")
        continue
    
    print(f"  找到 {len(ts_files)} 个 ts 文件")
    
    # 从不同的 ts 文件生成封面
    generated = 0
    for i, ts_file in enumerate(ts_files[:10], 1):
        if not ts_file.strip():
            continue
        ts_file = ts_file.strip()
        
        cover_path = f'/www/wwwroot/video-app/backend/uploads/hls/{video}/covers/cover_{i}.webp'
        
        # 使用 ffmpeg 生成封面
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -ss 1 -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 -y \\"{cover_path}\\" 2>&1"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
        output = stdout.read().decode('utf-8', errors='replace')
        
        # 检查是否生成成功
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{cover_path}\\" && echo yes || echo no"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        exists = stdout.read().decode('utf-8', errors='replace').strip()
        
        if exists == 'yes':
            generated += 1
            print(f"  生成 cover_{i}.webp")
        else:
            # 如果失败，尝试不同的位置
            for pos in [0, 2, 5]:
                cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -ss {pos} -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 -y \\"{cover_path}\\" 2>&1"'
                ssh.exec_command(cmd, timeout=120)
                
                cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{cover_path}\\" && echo yes || echo no"'
                stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
                exists = stdout.read().decode('utf-8', errors='replace').strip()
                
                if exists == 'yes':
                    generated += 1
                    print(f"  生成 cover_{i}.webp (pos={pos})")
                    break
    
    print(f"  完成: 生成了 {generated} 个封面")
    processed += 1
    
    # 限制处理数量
    if processed >= 10:
        print("\n已处理 10 个视频，暂停...")
        break

# 验证结果
print("\n\n验证结果...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "for d in /www/wwwroot/video-app/backend/uploads/hls/*/covers; do echo \\"$(basename $(dirname $d)): $(ls $d/*.webp 2>/dev/null | wc -l) covers\\"; done | tail -10"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
result = stdout.read().decode('utf-8', errors='replace')
print(result)

ssh.close()
print("\n完成！")
