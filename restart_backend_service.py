#!/usr/bin/env python3
"""重启主服务器后端服务"""
import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    print('🔄 重启后端服务...')
    stdin, stdout, stderr = ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl restart video-app-backend.service"',
        timeout=60
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if out:
        print(f'  输出: {out}')
    if err:
        print(f'  错误: {err}')
    
    import time
    time.sleep(3)
    
    print('\n📊 检查服务状态...')
    stdin, stdout, stderr = ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl is-active video-app-backend.service"',
        timeout=30
    )
    status = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f'  服务状态: {status}')
    
    print('\n🧪 测试 API...')
    stdin, stdout, stderr = ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/health"',
        timeout=30
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    print(f'  健康检查: {out}')
    
    # 测试新的待处理视频 API
    print('\n🧪 测试待处理视频 API...')
    stdin, stdout, stderr = ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/admin/videos/pending"',
        timeout=30
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    print(f'  待处理视频: {out[:200]}...' if len(out) > 200 else f'  待处理视频: {out}')
    
    ssh.close()
    print('\n✅ 完成!')

if __name__ == '__main__':
    main()
