#!/usr/bin/env python3
"""查找缺失的HLS文件"""
import subprocess

# 获取视频134, 135, 138的标题
cmd = '''PGPASSWORD=VideoApp2024! psql -h 127.0.0.1 -U video_app -d video_app -t -c "SELECT id, title FROM videos WHERE id IN (134, 135, 138);"'''
result = subprocess.run(
    ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
     'root@38.47.218.137', cmd],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print("=== 视频标题 ===")
print(result.stdout)

# 列出所有中文目录
print("\n=== 剩余中文目录 ===")
cmd = 'ls -la /www/wwwroot/video-app/backend/uploads/hls/ | grep -v "^d.*[0-9]$"'
result = subprocess.run(
    ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
     'root@38.47.218.137', cmd],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
