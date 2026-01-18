#!/usr/bin/env python3
"""监控 v2 处理进度"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('📊 处理进度')
print('=' * 60)

# 检查 downloads
print('\n📁 Downloads:')
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
short = stdout.read().decode('gbk', errors='ignore').strip()
print(f'  short: {short if short else "(empty)"}')

stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\long\\*.mp4 /b 2>nul', timeout=30)
long = stdout.read().decode('gbk', errors='ignore').strip()
print(f'  long: {long if long else "(empty)"}')

# 检查 processing
print('\n📁 Processing:')
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
proc = stdout.read().decode('gbk', errors='ignore').strip()
print(f'  {proc if proc else "(empty)"}')

# 检查日志
print('\n📝 Watcher Log:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 15"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
for line in log.split('\n')[-15:]:
    print(f'  {line}')

# 检查转码日志
print('\n📝 Transcode Log:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 10"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
for line in log.split('\n')[-10:]:
    print(f'  {line}')

# FFmpeg 进程
print('\n🔄 FFmpeg:')
stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe" /FO CSV /NH', timeout=30)
output = stdout.read().decode('gbk', errors='ignore')
if 'ffmpeg.exe' in output:
    print('  Running')
else:
    print('  Not running')

ssh.close()
