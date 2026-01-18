#!/usr/bin/env python3
"""验证文件是否存在"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 使用Python脚本在服务器上验证
verify_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import psycopg2

base_path = '/www/wwwroot/video-app/backend/uploads'

conn = psycopg2.connect(host='localhost', database='video_app', user='video_app', password='VideoApp2024!')
cur = conn.cursor()
cur.execute("SELECT id, title, cover_url, hls_url FROM videos WHERE id >= 102 ORDER BY id")
rows = cur.fetchall()

for row in rows:
    video_id, title, cover_url, hls_url = row
    print(f"\\n视频 {video_id}: {title[:40]}...")
    
    # 检查封面
    if cover_url:
        cover_path = base_path + cover_url.replace('/uploads', '')
        if os.path.exists(cover_path):
            size = os.path.getsize(cover_path)
            print(f"  封面: OK ({size} bytes)")
        else:
            print(f"  封面: 不存在 - {cover_path}")
    
    # 检查HLS
    if hls_url:
        hls_path = base_path + hls_url.replace('/uploads', '')
        if os.path.exists(hls_path):
            print(f"  HLS: OK")
            # 检查720p目录
            hls_dir = os.path.dirname(hls_path)
            p720 = os.path.join(hls_dir, '720p')
            if os.path.exists(p720):
                files = os.listdir(p720)
                print(f"  720p: {len(files)} files")
        else:
            print(f"  HLS: 不存在 - {hls_path}")

cur.close()
conn.close()
'''

print("验证文件...")
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.py', delete=False) as f:
    f.write(verify_script)
    temp_file = f.name

sftp = ssh.open_sftp()
sftp.put(temp_file, 'D:/verify_files.py')
sftp.close()
os.unlink(temp_file)

cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no D:\\verify_files.py root@{MAIN_HOST}:/tmp/verify_files.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PYTHONIOENCODING=utf-8 python3 /tmp/verify_files.py"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
error = stderr.read().decode('utf-8', errors='replace')
print(output)
if error:
    print(f"错误: {error}")

ssh.close()
