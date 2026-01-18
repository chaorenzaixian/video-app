#!/usr/bin/env python3
"""读取完整的 watcher 脚本"""
import paramiko

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    sftp = ssh.open_sftp()
    with sftp.file('D:\\VideoTranscode\\scripts\\watcher.ps1', 'r') as f:
        content = f.read().decode('utf-8', errors='ignore')
    sftp.close()
    
    # 找到上传部分（大约在 140-180 行）
    lines = content.split('\n')
    print('=== 上传部分代码 (行 135-200) ===')
    for i in range(134, min(200, len(lines))):
        print(f'{i+1}: {lines[i]}')
    
    ssh.close()

if __name__ == '__main__':
    main()
