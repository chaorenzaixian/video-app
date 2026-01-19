#!/usr/bin/env python3
"""上传封面文件到主服务器"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

print('=' * 70)
print('上传封面文件到主服务器')
print('=' * 70)

# 1. 在主服务器创建covers目录
print('\n1. 创建covers目录...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "mkdir -p /www/wwwroot/video-app/backend/uploads/hls/140/covers"'
stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "& {cmd}"', timeout=60)
stdout.read()
print('目录已创建')

# 2. 复制封面到临时目录
print('\n2. 复制封面到临时目录...')
ps_cmd = '''
$dirs = Get-ChildItem -Path "D:\\VideoTranscode\\completed\\long" -Directory | Where-Object { $_.Name -like "*小美女*宿舍*" }
if ($dirs) {
    $coversDir = Join-Path $dirs[0].FullName "covers"
    $tempDir = "D:\\VideoTranscode\\temp_covers"
    if (Test-Path $tempDir) { Remove-Item -Path $tempDir -Recurse -Force }
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    Copy-Item -Path "$coversDir\\*" -Destination $tempDir -Force
    Write-Output "Copied: $((Get-ChildItem $tempDir).Count) files"
}
'''
stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "{ps_cmd}"', timeout=60)
output = stdout.read().decode('gbk', errors='replace').strip()
print(output)

# 3. 上传封面文件
print('\n3. 上传封面文件...')
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-ChildItem D:\\VideoTranscode\\temp_covers -File | ForEach-Object { Write-Output $_.Name; scp -i C:\\server_key -o StrictHostKeyChecking=no $_.FullName root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/hls/140/covers/ }"', timeout=300)
time.sleep(30)
output = stdout.read().decode('gbk', errors='replace').strip()
print(f'上传: {output}')

# 4. 验证上传
print('\n4. 验证上传...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/hls/140/covers/"'
stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "& {cmd}"', timeout=60)
output = stdout.read().decode('utf-8', errors='replace').strip()
print(output)

# 5. 设置权限
print('\n5. 设置权限...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "chown -R www:www /www/wwwroot/video-app/backend/uploads/hls/140/covers/"'
stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "& {cmd}"', timeout=60)
stdout.read()
print('权限已设置')

ssh.close()
print('\n完成!')
