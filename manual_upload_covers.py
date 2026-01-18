#!/usr/bin/env python3
"""手动为已有视频上传封面（从转码服务器的备份中恢复）"""
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

print("检查转码服务器上是否有可用的封面...")
print("=" * 60)

# 检查 output 目录
cmd = 'dir /b "D:\\VideoTranscode\\output" 2>nul'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output_dirs = stdout.read().decode('utf-8', errors='replace').strip()

if not output_dirs:
    print("output 目录为空，检查是否有备份...")
    
    # 检查是否有其他位置的封面
    cmd = 'dir /s /b "D:\\VideoTranscode\\*.webp" 2>nul | head -20'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    webp_files = stdout.read().decode('utf-8', errors='replace').strip()
    if webp_files:
        print(f"找到 webp 文件:\n{webp_files}")
    else:
        print("没有找到任何 webp 文件")
else:
    print(f"output 目录内容:\n{output_dirs}")
    
    # 检查每个目录的 covers
    for dir_name in output_dirs.split('\n'):
        if not dir_name.strip():
            continue
        dir_name = dir_name.strip()
        cmd = f'dir /b "D:\\VideoTranscode\\output\\{dir_name}\\covers" 2>nul'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        covers = stdout.read().decode('utf-8', errors='replace').strip()
        if covers:
            print(f"\n{dir_name}/covers: {covers}")

# 检查主服务器上需要封面的视频
print("\n\n检查主服务器上需要封面的视频...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
hls_videos = stdout.read().decode('utf-8', errors='replace').strip().split('\n')

print(f"HLS 视频数量: {len(hls_videos)}")

# 检查哪些视频没有 covers 目录
videos_without_covers = []
for video in hls_videos[:10]:  # 只检查前10个
    if not video.strip():
        continue
    video = video.strip()
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/ 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    count = stdout.read().decode('utf-8', errors='replace').strip()
    if count == '0' or not count:
        videos_without_covers.append(video)
        print(f"  {video}: 无封面")
    else:
        print(f"  {video}: {count} 个封面")

print(f"\n需要封面的视频: {len(videos_without_covers)}")

# 由于转码服务器上的输出目录已清空，我们需要重新生成封面
# 或者从主服务器的 HLS 文件中提取封面

if videos_without_covers:
    print("\n\n方案：从主服务器的 HLS 视频中重新生成封面")
    print("这需要在主服务器上运行 ffmpeg...")
    
    # 创建一个脚本在主服务器上运行
    generate_script = '''#!/bin/bash
# 为视频生成多封面
VIDEO_NAME="$1"
HLS_DIR="/www/wwwroot/video-app/backend/uploads/hls/$VIDEO_NAME"
COVERS_DIR="$HLS_DIR/covers"

# 检查 master.m3u8 是否存在
if [ ! -f "$HLS_DIR/master.m3u8" ]; then
    echo "Error: master.m3u8 not found"
    exit 1
fi

# 找到第一个 ts 文件
TS_FILE=$(ls "$HLS_DIR"/*.ts 2>/dev/null | head -1)
if [ -z "$TS_FILE" ]; then
    # 尝试从子目录找
    TS_FILE=$(ls "$HLS_DIR"/*/*.ts 2>/dev/null | head -1)
fi

if [ -z "$TS_FILE" ]; then
    echo "Error: No ts files found"
    exit 1
fi

# 获取视频时长
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TS_FILE" 2>/dev/null)
if [ -z "$DURATION" ]; then
    DURATION=60
fi

# 创建 covers 目录
mkdir -p "$COVERS_DIR"

# 生成 10 张封面
for i in $(seq 1 10); do
    POS=$(echo "$DURATION * $i / 11" | bc -l)
    ffmpeg -ss $POS -i "$TS_FILE" -vframes 1 -vf "scale=640:-1" -c:v libwebp -quality 85 -y "$COVERS_DIR/cover_$i.webp" 2>/dev/null
done

echo "Generated covers for $VIDEO_NAME"
ls -la "$COVERS_DIR"
'''
    
    # 上传脚本到主服务器
    print("上传封面生成脚本到主服务器...")
    script_path = '/tmp/generate_covers.sh'
    
    # 通过 SSH 创建脚本
    cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cat > {script_path}" << 'SCRIPT'
{generate_script}
SCRIPT'''
    
    # 使用 echo 方式
    escaped_script = generate_script.replace('"', '\\"').replace('$', '\\$')
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "echo \\"{escaped_script}\\" > {script_path} && chmod +x {script_path}"'
    
    # 简化：直接在主服务器上执行命令
    for video in videos_without_covers[:3]:  # 先测试3个
        print(f"\n为 {video} 生成封面...")
        
        # 创建 covers 目录
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/{video}/covers"'
        ssh.exec_command(cmd, timeout=60)
        
        # 找到 ts 文件
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/*.ts 2>/dev/null | head -1"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        ts_file = stdout.read().decode('utf-8', errors='replace').strip()
        
        if not ts_file:
            # 尝试子目录
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls /www/wwwroot/video-app/backend/uploads/hls/{video}/*/*.ts 2>/dev/null | head -1"'
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            ts_file = stdout.read().decode('utf-8', errors='replace').strip()
        
        if not ts_file:
            print(f"  跳过：没有找到 ts 文件")
            continue
        
        print(f"  使用 ts 文件: {ts_file}")
        
        # 生成封面
        for i in range(1, 11):
            pos = i * 5  # 每5秒一张
            cover_path = f'/www/wwwroot/video-app/backend/uploads/hls/{video}/covers/cover_{i}.webp'
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ffmpeg -ss {pos} -i \\"{ts_file}\\" -vframes 1 -vf \\"scale=640:-1\\" -c:v libwebp -quality 85 -y \\"{cover_path}\\" 2>/dev/null"'
            ssh.exec_command(cmd, timeout=120)
        
        # 验证
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -la /www/wwwroot/video-app/backend/uploads/hls/{video}/covers/"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        result = stdout.read().decode('utf-8', errors='replace')
        print(f"  结果: {result[:200]}")

ssh.close()
print("\n完成")
