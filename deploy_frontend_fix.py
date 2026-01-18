#!/usr/bin/env python3
"""修复并重新部署前端"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 读取修复后的文件
with open('frontend/src/views/admin/TranscodeMonitor.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 保存到转码服务器
sftp = ssh.open_sftp()
with sftp.file('D:\\temp_TranscodeMonitor.vue', 'w') as f:
    f.write(content)
sftp.close()

print('1. 上传修复后的文件...')
cmd = 'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\temp_TranscodeMonitor.vue" root@38.47.218.137:/www/wwwroot/video-app/frontend/src/views/admin/TranscodeMonitor.vue'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='ignore'))

print('\n2. 重新构建前端...')
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cd /www/wwwroot/video-app/frontend && npm run build 2>&1"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
out = stdout.read().decode('utf-8', errors='ignore')
if 'error' in out.lower():
    print('构建失败:')
    print(out[-2000:])
else:
    print('✓ 前端构建成功')

ssh.close()
print('\n✅ 完成!')
