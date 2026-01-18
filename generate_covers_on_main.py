#!/usr/bin/env python3
"""在主服务器上为视频生成多封面"""
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

# 创建封面生成脚本
generate_script = '''#!/bin/bash
# 为所有没有封面的视频生成多封面

HLS_BASE="/www/wwwroot/video-app/backend/uploads/hls"

for VIDEO_DIR in "$HLS_BASE"/*/; do
    VIDEO_NAME=$(basename "$VIDEO_DIR")
    COVERS_DIR="$VIDEO_DIR/covers"
    
    # 跳过已有封面的视频
    if [ -d "$COVERS_DIR" ] && [ "$(ls -A $COVERS_DIR 2>/dev/null)" ]; then
        echo "Skip: $VIDEO_NAME (already has covers)"
        continue
    fi
    
    # 检查是否有 master.m3u8
    if [ ! -f "$VIDEO_DIR/master.m3u8" ]; then
        echo "Skip: $VIDEO_NAME (no master.m3u8)"
        continue
    fi
    
    echo "Processing: $VIDEO_NAME"
    
    # 找到所有 ts 文件并合并成一个列表
    TS_FILES=$(find "$VIDEO_DIR" -name "*.ts" -type f | sort | head -20)
    
    if [ -z "$TS_FILES" ]; then
        echo "  Error: No ts files found"
        continue
    fi
    
    # 创建 covers 目录
    mkdir -p "$COVERS_DIR"
    
    # 从不同的 ts 文件中提取封面
    i=1
    for TS_FILE in $TS_FILES; do
        if [ $i -gt 10 ]; then
            break
        fi
        
        COVER_PATH="$COVERS_DIR/cover_$i.webp"
        
        # 从 ts 文件的第 1 秒提取帧
        ffmpeg -ss 1 -i "$TS_FILE" -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y "$COVER_PATH" 2>/dev/null
        
        if [ -f "$COVER_PATH" ]; then
            echo "  Generated: cover_$i.webp"
            i=$((i + 1))
        fi
    done
    
    # 如果封面不足 10 张，从第一个 ts 文件的不同位置提取
    FIRST_TS=$(echo "$TS_FILES" | head -1)
    while [ $i -le 10 ]; do
        COVER_PATH="$COVERS_DIR/cover_$i.webp"
        POS=$((i * 2))
        ffmpeg -ss $POS -i "$FIRST_TS" -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y "$COVER_PATH" 2>/dev/null
        
        if [ -f "$COVER_PATH" ]; then
            echo "  Generated: cover_$i.webp (from pos $POS)"
        fi
        i=$((i + 1))
    done
    
    # 显示结果
    COVER_COUNT=$(ls "$COVERS_DIR"/*.webp 2>/dev/null | wc -l)
    echo "  Total covers: $COVER_COUNT"
done

echo "Done!"
'''

# 上传并执行脚本
print("上传脚本到主服务器...")

# 先写入本地临时文件
with open('temp_generate_covers.sh', 'w', newline='\n') as f:
    f.write(generate_script)

# 通过 scp 上传
cmd = f'scp -i {SSH_KEY} -o StrictHostKeyChecking=no temp_generate_covers.sh {MAIN_USER}@{MAIN_HOST}:/tmp/generate_covers.sh'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
err = stderr.read().decode('utf-8', errors='replace')
if err and 'error' in err.lower():
    print(f"上传错误: {err}")
else:
    print("脚本已上传")

# 执行脚本
print("\n执行封面生成脚本（这可能需要几分钟）...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "chmod +x /tmp/generate_covers.sh && /tmp/generate_covers.sh"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)

# 实时输出
output = stdout.read().decode('utf-8', errors='replace')
print(output)

err = stderr.read().decode('utf-8', errors='replace')
if err:
    print(f"错误: {err[:500]}")

# 验证结果
print("\n\n验证结果...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -d /www/wwwroot/video-app/backend/uploads/hls/*/covers 2>/dev/null | wc -l"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
count = stdout.read().decode('utf-8', errors='replace').strip()
print(f"有 covers 目录的视频数量: {count}")

# 检查几个具体的视频
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/ | tail -5"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
videos = stdout.read().decode('utf-8', errors='replace').strip().split('\n')

for video in videos:
    if not video.strip():
        continue
    video = video.strip()
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/ 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    cover_count = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"  {video}: {cover_count} 个封面")

ssh.close()

# 清理临时文件
import os
if os.path.exists('temp_generate_covers.sh'):
    os.remove('temp_generate_covers.sh')

print("\n完成！")
