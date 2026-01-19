#!/usr/bin/env python3
"""检查封面生成情况"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('=' * 70)
print('检查封面生成情况')
print('=' * 70)

# 1. 检查转码脚本中的封面生成逻辑
print('\n1. 检查transcode_full.ps1中的封面生成...')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-String -Pattern \'cover|Cover|thumbnail\' -Context 2,2"', timeout=60)
output = stdout.read().decode('gbk', errors='replace').strip()
print(output[:2000] if output else '无匹配')

# 2. 检查已完成目录中的封面文件
print('\n2. 检查已完成目录中的封面文件...')
stdin, stdout, stderr = ssh.exec_command('cmd /c dir /s /b "D:\\VideoTranscode\\completed\\long\\*cover*" 2>nul', timeout=60)
output = stdout.read().decode('gbk', errors='replace').strip()
print(output[:1500] if output else '无封面文件')

# 3. 检查一个具体目录的内容
print('\n3. 检查"身材极品"目录的内容...')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "$dirs = Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Where-Object { $_.Name -like \'*小美女*\' }; if ($dirs) { Get-ChildItem $dirs[0].FullName -Recurse | Select-Object FullName }"', timeout=60)
output = stdout.read().decode('gbk', errors='replace').strip()
print(output[:1500] if output else '无内容')

ssh.close()
print('\n完成!')
