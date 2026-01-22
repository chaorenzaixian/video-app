#!/usr/bin/env python3
"""重新部署watcher脚本到转码服务器"""
import paramiko
import os

# 转码服务器配置
TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def deploy():
    # 读取本地脚本
    script_path = os.path.join(os.path.dirname(__file__), "watcher_complete.ps1")
    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 连接服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 上传脚本
    sftp = ssh.open_sftp()
    
    remote_path = "D:/VideoTranscode/scripts/watcher.ps1"
    print(f"上传脚本到 {remote_path}...")
    
    with sftp.file(remote_path, 'w') as f:
        f.write(script_content)
    
    sftp.close()
    
    print("脚本上传完成!")
    
    # 验证
    stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "Get-Content \'{remote_path}\' | Select-Object -First 5"')
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"验证前5行:\n{output}")
    
    ssh.close()
    print("部署完成!")

if __name__ == "__main__":
    deploy()
