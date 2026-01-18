#!/usr/bin/env python3
"""通过转码服务器部署监控API到主服务器"""
import paramiko
import time

# 转码服务器配置
TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

# 主服务器配置
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
MAIN_KEY = 'C:\\server_key'
BACKEND_PATH = '/www/wwwroot/video-app/backend'

# 需要部署的文件
FILES_TO_DEPLOY = [
    {
        'local': 'backend/app/api/transcode_monitor.py',
        'remote': f'{BACKEND_PATH}/app/api/transcode_monitor.py'
    },
    {
        'local': 'backend/app/api/__init__.py',
        'remote': f'{BACKEND_PATH}/app/api/__init__.py'
    }
]

def main():
    print("=" * 60)
    print("部署转码监控API到主服务器")
    print("=" * 60)
    
    # 连接转码服务器
    print("\n1. 连接转码服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
    print("   ✓ 已连接")
    
    sftp = ssh.open_sftp()
    
    # 部署文件
    print("\n2. 部署文件...")
    for file_info in FILES_TO_DEPLOY:
        local_path = file_info['local']
        remote_path = file_info['remote']
        
        print(f"\n   📄 {local_path}")
        
        # 读取本地文件
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 保存到转码服务器临时文件
        temp_name = local_path.split('/')[-1]
        temp_path = f'D:\\temp_{temp_name}'
        with sftp.file(temp_path, 'w') as f:
            f.write(content)
        print(f"      → 已保存到转码服务器: {temp_path}")
        
        # 通过SCP上传到主服务器
        scp_cmd = f'scp -i {MAIN_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "{temp_path}" {MAIN_USER}@{MAIN_HOST}:{remote_path}'
        stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=60)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        
        if 'Permission denied' in err or 'No such file' in err:
            print(f"      ✗ 上传失败: {err}")
        else:
            print(f"      ✓ 已上传到主服务器: {remote_path}")
        
        # 清理临时文件
        ssh.exec_command(f'del "{temp_path}"')
    
    sftp.close()
    
    # 重启后端服务
    print("\n3. 重启后端服务...")
    
    # 使用systemctl重启
    restart_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "systemctl restart video-app-backend 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(restart_cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(f"   输出: {out}")
    if err:
        print(f"   错误: {err}")
    
    # 等待服务启动
    print("\n4. 等待服务启动...")
    time.sleep(5)
    
    # 检查服务状态
    print("\n5. 检查服务状态...")
    status_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "systemctl status video-app-backend | head -15"'
    stdin, stdout, stderr = ssh.exec_command(status_cmd, timeout=30)
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 测试API
    print("\n6. 测试转码监控API...")
    test_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "curl -s http://localhost:5000/api/admin/transcode/status -H \'X-Transcode-Key: test\' | head -200"'
    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=30)
    response = stdout.read().decode('utf-8', errors='ignore')
    print(f"   响应: {response[:300]}...")
    
    ssh.close()
    print("\n" + "=" * 60)
    print("部署完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
