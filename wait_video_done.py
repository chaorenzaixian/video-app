#!/usr/bin/env python3
"""等待视频处理完成"""
import paramiko
import time

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    print('等待视频处理完成...')
    for i in range(18):  # 最多等待 3 分钟
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 15"', timeout=30)
        out = stdout.read().decode('utf-8', errors='ignore')
        
        if 'new_test_' in out and ('Done:' in out or 'Callback OK' in out):
            print('\n✅ 处理完成!')
            print(out)
            break
        
        print(f'  等待中... ({i+1}/18)')
        time.sleep(10)
    
    # 检查数据库
    print('\n检查待处理视频...')
    cmd = '''ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -c \\"SELECT id, title, status, created_at FROM videos WHERE status='REVIEWING' ORDER BY created_at DESC LIMIT 5;\\""'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
