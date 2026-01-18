#!/usr/bin/env python3
"""调试转码 v2"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('🔍 调试转码 v2')
print('=' * 60)

# 检查脚本是否存在
print('\n📄 检查脚本:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "(Get-Item D:\\VideoTranscode\\scripts\\transcode_v2.ps1).Length"', timeout=30)
size = stdout.read().decode('utf-8', errors='ignore').strip()
print(f'  transcode_v2.ps1 大小: {size} bytes')

# 检查脚本内容
print('\n📄 脚本开头:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_v2.ps1 -Head 10"', timeout=30)
content = stdout.read().decode('utf-8', errors='ignore').strip()
print(content[:500] if content else '(empty)')

# 手动测试转码脚本
print('\n🧪 手动测试转码脚本:')

# 先找一个测试文件
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b 2>nul', timeout=30)
files = stdout.read().decode('gbk', errors='ignore').strip()
if files:
    test_file = files.split('\n')[0].strip()
    print(f'  测试文件: {test_file}')
    
    # 复制到 downloads/long 测试
    print('  复制到 downloads/long...')
    stdin, stdout, stderr = ssh.exec_command(f'copy "D:\\VideoTranscode\\completed\\short\\{test_file}" "D:\\VideoTranscode\\downloads\\long\\test_hls.mp4"', timeout=30)
    stdout.read()
    
    # 检查是否复制成功
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\long\\*.mp4 /b 2>nul', timeout=30)
    copied = stdout.read().decode('gbk', errors='ignore').strip()
    print(f'  复制结果: {copied}')

# 检查 watcher 日志
print('\n📝 Watcher 日志:')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"', timeout=30)
log = stdout.read().decode('utf-8', errors='ignore').strip()
for line in log.split('\n')[-20:]:
    print(f'  {line}')

ssh.close()
