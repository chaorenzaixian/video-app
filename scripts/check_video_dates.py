#!/usr/bin/env python3
"""检查视频的日期时间"""
import subprocess

cmd = '''PGPASSWORD=VideoApp2024! psql -h 127.0.0.1 -U video_app -d video_app -c "SELECT id, LEFT(title, 20) as title, duration, created_at, published_at FROM videos ORDER BY id DESC LIMIT 10;"'''

result = subprocess.run(
    ["ssh", "-i", "server_key_main", "-o", "StrictHostKeyChecking=no", 
     "root@38.47.218.137", cmd],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
