#!/usr/bin/env python3
"""验证HLS目录"""
import subprocess

video_ids = [111, 119, 120, 124, 134, 135, 136, 137, 138, 139, 140]

print("=== 验证HLS目录 ===")
for vid in video_ids:
    cmd = f'ls /www/wwwroot/video-app/backend/uploads/hls/{vid}/ 2>/dev/null | head -3'
    result = subprocess.run(
        ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
         'root@38.47.218.137', cmd],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    files = result.stdout.strip()
    if files:
        print(f"  ✓ {vid}: {files.replace(chr(10), ', ')}")
    else:
        print(f"  ✗ {vid}: 空目录或不存在")
