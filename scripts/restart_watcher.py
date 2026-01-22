#!/usr/bin/env python3
"""重启watcher服务"""
import paramiko
import time

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def restart():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 1. 停止所有ffmpeg进程
    print("\n=== 停止FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM ffmpeg.exe')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 2. 停止所有PowerShell进程（watcher）
    print("\n=== 停止Watcher进程 ===")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 3. 把processing目录的文件移回downloads/long
    print("\n=== 恢复processing中的文件 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\processing\\*.mp4 | Move-Item -Destination D:\\VideoTranscode\\downloads\\long\\ -Force"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace') or "完成")
    
    # 4. 等待一下
    print("\n等待2秒...")
    time.sleep(2)
    
    # 5. 启动新的watcher
    print("\n=== 启动新Watcher ===")
    cmd = 'powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1\' -WindowStyle Normal"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace') or "已启动")
    
    # 6. 等待启动
    time.sleep(3)
    
    # 7. 验证
    print("\n=== 验证进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 8. 检查downloads目录
    print("\n=== Downloads/long目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\downloads\\long\\*.mp4')
    print(stdout.read().decode('utf-8', errors='replace') or "空")
    
    ssh.close()
    print("\n重启完成！新的单分辨率模式已生效。")

if __name__ == "__main__":
    restart()
