#!/usr/bin/env python3
"""移动input目录的视频到downloads/long"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def move_videos():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 列出input目录的文件
    print("=== Input目录文件 ===")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\input\\*.mp4')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 移动文件到downloads/long
    print("\n=== 移动文件到downloads/long ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\input\\*.mp4 | Move-Item -Destination D:\\VideoTranscode\\downloads\\long\\ -Force"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print(f"Error: {err}")
    
    # 确认移动成功
    print("\n=== 确认downloads/long目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\long\\*.mp4')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()
    print("\n完成！视频已移动到downloads/long，watcher将自动开始处理")

if __name__ == "__main__":
    move_videos()
