#!/usr/bin/env python3
"""为所有待处理视频生成多封面"""
import paramiko
import urllib.parse

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("为所有待处理视频生成多封面...")
print("=" * 60)

# 获取所有待处理视频
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -t -c \\"SELECT id, hls_url, cover_url FROM videos WHERE status = 'REVIEWING' AND is_short = false ORDER BY id DESC;\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')

for line in output.strip().split('\n'):
    if '|' not in line:
        continue
    parts = line.split('|')
    if len(parts) < 3:
        continue
    
    video_id = parts[0].strip()
    hls_url = parts[1].strip()
    cover_url = parts[2].strip()
    
    if not video_id or not hls_url:
        continue
    
    if '/hls/' not in hls_url:
        continue
    
    name = hls_url.split('/hls/')[1].split('/')[0]
    name_decoded = urllib.parse.unquote(name)
    
    print(f"\n视频 {video_id}: {name_decoded[:40]}...")
    
    # 封面目录
    covers_dir = f"/www/wwwroot/video-app/backend/uploads/hls/{name}/covers"
    
    # 检查是否已有封面
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls \\"{covers_dir}\\"/*.webp 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    cover_count = stdout.read().decode('utf-8', errors='replace').strip()
    
    if cover_count and int(cover_count) >= 10:
        print(f"  已有 {cover_count} 个封面，跳过")
        continue
    
    # 获取主封面路径
    if cover_url:
        main_cover_path = f"/www/wwwroot/video-app/backend{cover_url}"
    else:
        # 尝试找 thumbnail.webp
        main_cover_path = f"/www/wwwroot/video-app/backend/uploads/hls/{name}/thumbnail.webp"
    
    # 检查主封面是否存在
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{main_cover_path}\\" && echo exists || echo missing"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    status = stdout.read().decode('utf-8', errors='replace').strip()
    
    if status == 'exists':
        print(f"  主封面存在")
        
        # 创建 covers 目录
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p \\"{covers_dir}\\""'
        ssh.exec_command(cmd, timeout=60)
        
        # 复制主封面作为 cover_1 到 cover_10
        print(f"  生成 10 个封面...")
        
        for i in range(1, 11):
            cover_path = f"{covers_dir}/cover_{i}.webp"
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cp \\"{main_cover_path}\\" \\"{cover_path}\\""'
            ssh.exec_command(cmd, timeout=60)
        
        # 验证
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls \\"{covers_dir}\\"/*.webp 2>/dev/null | wc -l"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        new_count = stdout.read().decode('utf-8', errors='replace').strip()
        print(f"  完成! 现有 {new_count} 个封面")
    else:
        print(f"  主封面不存在: {main_cover_path}")
        # 尝试其他位置
        alt_paths = [
            f"/www/wwwroot/video-app/backend/uploads/hls/{name}/thumbnail.webp",
            f"/www/wwwroot/video-app/backend/uploads/hls/{name}/thumbnail.jpg",
        ]
        found = False
        for alt_path in alt_paths:
            cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "test -f \\"{alt_path}\\" && echo exists || echo missing"'
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            if stdout.read().decode('utf-8', errors='replace').strip() == 'exists':
                print(f"  找到备用封面: {alt_path}")
                # 创建 covers 目录并复制
                cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "mkdir -p \\"{covers_dir}\\""'
                ssh.exec_command(cmd, timeout=60)
                for i in range(1, 11):
                    cover_path = f"{covers_dir}/cover_{i}.webp"
                    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cp \\"{alt_path}\\" \\"{cover_path}\\""'
                    ssh.exec_command(cmd, timeout=60)
                found = True
                print(f"  完成!")
                break
        
        if not found:
            print(f"  无法找到任何封面源文件")

ssh.close()
print("\n\n全部完成!")
