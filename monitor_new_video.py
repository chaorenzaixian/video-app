#!/usr/bin/env python3
"""监控新视频处理进度"""
import paramiko
import time

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    print('📜 监控 Watcher 日志...\n')
    
    for i in range(12):  # 最多等待 2 分钟
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"', timeout=30)
        out = stdout.read().decode('utf-8', errors='ignore')
        
        print(f'--- 第 {i+1} 次检查 ---')
        lines = out.strip().split('\n')
        for line in lines[-10:]:
            print(f'  {line}')
        
        # 检查是否有新视频处理完成
        if 'new_test_' in out and 'Done:' in out:
            print('\n✅ 新视频处理完成！')
            break
        elif 'new_test_' in out and 'Callback OK' in out:
            print('\n✅ 回调成功！视频已添加到待处理列表')
            break
        
        print()
        time.sleep(10)
    
    # 检查数据库中的待处理视频
    print('\n📊 检查数据库中的待处理视频...')
    cmd = '''ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -c \\"SELECT id, title, status, created_at FROM videos WHERE status='REVIEWING' ORDER BY created_at DESC LIMIT 5;\\""'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='ignore')
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
