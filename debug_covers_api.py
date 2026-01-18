#!/usr/bin/env python3
"""调试封面 API"""
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

print("调试封面 API...")
print("=" * 60)

# 获取待处理视频
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -t -c \\"SELECT id, hls_url FROM videos WHERE status = 'REVIEWING' AND is_short = false LIMIT 1;\\""'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(f"待处理视频: {output}")

if '|' in output:
    parts = output.split('|')
    video_id = parts[0].strip()
    hls_url = parts[1].strip()
    
    print(f"\n视频 ID: {video_id}")
    print(f"HLS URL: {hls_url}")
    
    # 从 hls_url 提取目录名
    if '/hls/' in hls_url:
        name = hls_url.split('/hls/')[1].split('/')[0]
        name_decoded = urllib.parse.unquote(name)
        print(f"目录名: {name_decoded}")
        
        # 检查 covers 目录
        covers_dir = f"/www/wwwroot/video-app/backend/uploads/hls/{name}/covers"
        print(f"\n检查 covers 目录: {covers_dir}")
        
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "ls -la \\"{covers_dir}\\" 2>&1"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        output = stdout.read().decode('utf-8', errors='replace')
        print(output)
        
        # 测试 API
        print("\n测试 API...")
        test_script = f'''
import requests
import json

login_url = "http://localhost:8000/api/v1/auth/login"
resp = requests.post(login_url, json={{"username": "admin", "password": "admin123"}})
token = resp.json().get("access_token", "")

covers_url = "http://localhost:8000/api/v1/admin/videos/{video_id}/covers"
resp = requests.get(covers_url, headers={{"Authorization": f"Bearer {{token}}"}})
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
'''
        
        cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cd /www/wwwroot/video-app/backend && source venv/bin/activate && python3 -c \\"{test_script}\\""'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
        output = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        print(f"API 响应:\n{output}")
        if err:
            print(f"错误:\n{err}")

ssh.close()
