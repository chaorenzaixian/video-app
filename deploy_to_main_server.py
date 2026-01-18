#!/usr/bin/env python3
"""部署更新的代码到主服务器"""
import paramiko
import time

# 需要部署的文件
FILES_TO_DEPLOY = [
    {
        'local': 'backend/app/api/admin_video_ops.py',
        'remote': '/www/wwwroot/video-app/backend/app/api/admin_video_ops.py'
    },
    {
        'local': 'backend/app/api/transcode_callback.py',
        'remote': '/www/wwwroot/video-app/backend/app/api/transcode_callback.py'
    },
    {
        'local': 'backend/app/api/transcode_monitor.py',
        'remote': '/www/wwwroot/video-app/backend/app/api/transcode_monitor.py'
    },
    {
        'local': 'backend/app/api/__init__.py',
        'remote': '/www/wwwroot/video-app/backend/app/api/__init__.py'
    },
    {
        'local': 'frontend/src/views/admin/PendingVideoManage.vue',
        'remote': '/www/wwwroot/video-app/frontend/src/views/admin/PendingVideoManage.vue'
    },
    {
        'local': 'frontend/src/views/admin/TranscodeMonitor.vue',
        'remote': '/www/wwwroot/video-app/frontend/src/views/admin/TranscodeMonitor.vue'
    },
    {
        'local': 'frontend/src/router/index.js',
        'remote': '/www/wwwroot/video-app/frontend/src/router/index.js'
    },
    {
        'local': 'frontend/src/layouts/AdminLayout.vue',
        'remote': '/www/wwwroot/video-app/frontend/src/layouts/AdminLayout.vue'
    }
]

def main():
    # 连接到转码服务器
    transcode_ssh = paramiko.SSHClient()
    transcode_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    transcode_ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    print('🚀 部署代码到主服务器')
    print('=' * 60)
    
    # 读取本地文件并通过转码服务器上传到主服务器
    for file_info in FILES_TO_DEPLOY:
        local_path = file_info['local']
        remote_path = file_info['remote']
        
        print(f'\n📄 部署: {local_path}')
        
        # 读取本地文件
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 先保存到转码服务器的临时文件
        temp_path = f'D:\\temp_{local_path.split("/")[-1]}'
        sftp = transcode_ssh.open_sftp()
        with sftp.file(temp_path, 'w') as f:
            f.write(content)
        sftp.close()
        
        print(f'  ✓ 已保存到转码服务器: {temp_path}')
        
        # 通过 SCP 上传到主服务器
        cmd = f'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "{temp_path}" root@38.47.218.137:{remote_path}'
        stdin, stdout, stderr = transcode_ssh.exec_command(cmd, timeout=60)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        
        if 'Permission denied' in err or 'No such file' in err:
            print(f'  ✗ 上传失败: {err}')
        else:
            print(f'  ✓ 已上传到主服务器: {remote_path}')
        
        # 清理临时文件
        transcode_ssh.exec_command(f'del "{temp_path}"', timeout=10)
    
    # 重启后端服务
    print('\n🔄 重启后端服务...')
    
    # 检查服务管理方式
    stdin, stdout, stderr = transcode_ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "which supervisorctl pm2 systemctl 2>/dev/null"',
        timeout=30
    )
    tools = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f'  可用工具: {tools}')
    
    # 尝试使用 supervisorctl
    print('\n  尝试 supervisorctl...')
    stdin, stdout, stderr = transcode_ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "supervisorctl restart video-api 2>&1 || supervisorctl restart all 2>&1"',
        timeout=60
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(f'  输出: {out}')
    if err:
        print(f'  错误: {err}')
    
    # 重新构建前端
    print('\n🔨 重新构建前端...')
    stdin, stdout, stderr = transcode_ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "cd /www/wwwroot/video-app/frontend && npm run build 2>&1"',
        timeout=300
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    if 'error' in out.lower() or 'error' in err.lower():
        print(f'  ⚠️ 构建可能有问题: {out[-500:] if len(out) > 500 else out}')
    else:
        print(f'  ✓ 前端构建完成')
    
    # 等待服务启动
    print('\n⏳ 等待服务启动...')
    time.sleep(5)
    
    # 测试 API
    print('\n🧪 测试 API...')
    stdin, stdout, stderr = transcode_ssh.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/health"',
        timeout=30
    )
    out = stdout.read().decode('utf-8', errors='ignore')
    print(f'  健康检查: {out}')
    
    transcode_ssh.close()
    print('\n✅ 部署完成!')

if __name__ == '__main__':
    main()
