#!/usr/bin/env python3
"""部署前端转码监控页面"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'
FRONTEND_PATH = '/www/wwwroot/video-app/frontend'

# 需要部署的前端文件
FILES_TO_DEPLOY = [
    {
        'local': 'frontend/src/views/admin/TranscodeMonitor.vue',
        'remote': f'{FRONTEND_PATH}/src/views/admin/TranscodeMonitor.vue'
    }
]

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("OK")

sftp = ssh.open_sftp()

# 1. 部署文件
print("\n1. 部署前端文件...")
for file_info in FILES_TO_DEPLOY:
    local_path = file_info['local']
    remote_path = file_info['remote']
    
    print(f"   {local_path}")
    
    # 读取本地文件
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 保存到转码服务器临时文件
    temp_name = local_path.split('/')[-1]
    temp_path = f'D:\\temp_{temp_name}'
    with sftp.file(temp_path, 'w') as f:
        f.write(content)
    
    # 通过SCP上传到主服务器
    scp_cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no "{temp_path}" root@{MAIN_HOST}:{remote_path}'
    stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=60)
    err = stderr.read().decode()
    if 'Permission denied' in err:
        print(f"   ERROR: {err}")
    else:
        print(f"   OK -> {remote_path}")
    
    # 清理临时文件
    ssh.exec_command(f'del "{temp_path}"')

sftp.close()

# 2. 检查路由和菜单是否已配置
print("\n2. 检查路由配置...")
check_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "grep -c TranscodeMonitor {FRONTEND_PATH}/src/router/index.js"'
stdin, stdout, stderr = ssh.exec_command(check_cmd, timeout=30)
count = stdout.read().decode().strip()
if count and int(count) > 0:
    print(f"   OK - 路由已配置")
else:
    print(f"   WARNING - 路由可能未配置")

# 3. 重新构建前端
print("\n3. 重新构建前端...")
build_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "cd {FRONTEND_PATH} && npm run build 2>&1"'
stdin, stdout, stderr = ssh.exec_command(build_cmd, timeout=300)
out = stdout.read().decode()
if 'error' in out.lower():
    print(f"   WARNING: {out[-500:]}")
else:
    print(f"   OK - 构建完成")

# 4. 验证
print("\n4. 验证部署...")
verify_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "ls -la {FRONTEND_PATH}/dist/index.html"'
stdin, stdout, stderr = ssh.exec_command(verify_cmd, timeout=30)
print(f"   {stdout.read().decode().strip()}")

ssh.close()
print("\n部署完成!")
print("\n访问管理后台 -> 数据中心 -> 转码监控 查看效果")
