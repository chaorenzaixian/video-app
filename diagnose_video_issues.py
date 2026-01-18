#!/usr/bin/env python3
"""诊断视频问题"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("=" * 60)
print("1. 检查最新上传的视频记录")
print("=" * 60)
sql = "SELECT id, title, cover_url, hls_url, video_url, status, created_at FROM videos ORDER BY id DESC LIMIT 5;"
cmd = f"PGPASSWORD='VideoApp2024!' psql -h localhost -U video_app -d video_app -c \\\"{sql}\\\""
run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "{cmd}"'
stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("2. 检查主服务器上的HLS文件")
print("=" * 60)
cmd = "ls -la /www/wwwroot/video-app/backend/uploads/hls/ | tail -10"
run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "{cmd}"'
stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("3. 检查主服务器上的封面文件")
print("=" * 60)
cmd = "ls -la /www/wwwroot/video-app/backend/uploads/thumbnails/ | tail -10"
run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "{cmd}"'
stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("4. 检查转码服务器上的输出文件")
print("=" * 60)
cmd = 'dir /b D:\\VideoTranscode\\output\\ 2>nul || echo "No output files"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("5. 检查转码服务器上的HLS输出")
print("=" * 60)
cmd = 'dir /b D:\\VideoTranscode\\output\\hls\\ 2>nul || echo "No HLS files"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("6. 检查转码服务器上的封面输出")
print("=" * 60)
cmd = 'dir /b D:\\VideoTranscode\\output\\thumbnails\\ 2>nul || echo "No thumbnail files"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

print("=" * 60)
print("7. 检查watcher日志")
print("=" * 60)
cmd = 'type D:\\VideoTranscode\\logs\\watcher.log 2>nul | findstr /i "error upload" || echo "No errors found"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output[-3000:] if len(output) > 3000 else output)

print("=" * 60)
print("8. 检查最新的转码日志")
print("=" * 60)
cmd = 'for /f "delims=" %i in (\'dir /b /od D:\\VideoTranscode\\logs\\*.log 2^>nul ^| findstr /v watcher\') do @type "D:\\VideoTranscode\\logs\\%i" 2>nul | more +1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output[-2000:] if len(output) > 2000 else output)

ssh.close()
