#!/usr/bin/env python3
"""重启watcher并确保UTF-8编码"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 1. 停止所有PowerShell进程
print("1. 停止现有watcher进程...")
cmd = 'taskkill /F /IM powershell.exe 2>nul & echo Done'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

time.sleep(2)

# 2. 检查watcher脚本是否包含UTF-8修复
print("\n2. 检查watcher脚本...")
cmd = 'type D:\\VideoTranscode\\scripts\\watcher.ps1 | findstr "WebRequest charset"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"UTF-8相关代码: {output}")

if 'WebRequest' not in output:
    print("警告: watcher脚本可能没有UTF-8修复!")

# 3. 启动新的watcher
print("\n3. 启动新的watcher...")
# 使用计划任务启动
cmd = 'schtasks /Run /TN "VideoWatcher" 2>nul || start "watcher" powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

time.sleep(3)

# 4. 检查进程
print("\n4. 检查watcher进程...")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

# 5. 检查日志
print("\n5. 检查最新日志...")
cmd = 'type D:\\VideoTranscode\\logs\\watcher.log | findstr /n "." | findstr /r "^[0-9]*:" | more +1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
lines = output.strip().split('\n')
print('\n'.join(lines[-10:]))

# 6. 修复视频107
print("\n6. 修复视频107...")
fix_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2

title = '穿着小白袜的学妹，躲在卧室看黄片，结果被我发现了，被我狠狠的调教，顶级神仙身材，还是个小白虎'
hls_url = f'/uploads/hls/{title}/master.m3u8'
cover_url = f'/uploads/thumbnails/{title}.webp'
preview_url = f'/uploads/previews/{title}_preview.webm'

conn = psycopg2.connect(host='localhost', database='video_app', user='video_app', password='VideoApp2024!')
cur = conn.cursor()
cur.execute(
    "UPDATE videos SET title = %s, hls_url = %s, cover_url = %s, preview_url = %s WHERE id = 107",
    (title, hls_url, cover_url, preview_url)
)
conn.commit()
print(f"Updated: {cur.rowcount}")
cur.close()
conn.close()
'''

import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.py', delete=False) as f:
    f.write(fix_script)
    temp_file = f.name

sftp = ssh.open_sftp()
sftp.put(temp_file, 'D:/fix_107.py')
sftp.close()
os.unlink(temp_file)

cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no D:\\fix_107.py root@{MAIN_HOST}:/tmp/fix_107.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdout.read()

cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PYTHONIOENCODING=utf-8 python3 /tmp/fix_107.py"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

# 7. 检查是否还有其他乱码视频
print("\n7. 检查所有视频...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -t -c \'SELECT id, title FROM videos WHERE id > 100 ORDER BY id;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
print("\n完成!")
