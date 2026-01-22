#!/usr/bin/env python3
"""停止所有watcher进程"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def stop():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 先禁用Guardian任务
    print("=== 禁用Guardian任务 ===")
    stdin, stdout, stderr = ssh.exec_command('schtasks /change /tn WatcherGuardian /disable')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 停止所有FFmpeg进程
    print("\n=== 停止FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM ffmpeg.exe')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 删除lock文件
    print("\n=== 删除Lock文件 ===")
    stdin, stdout, stderr = ssh.exec_command('del /F D:\\VideoTranscode\\watcher.lock')
    print("Done")
    
    # 停止所有PowerShell进程
    print("\n=== 停止PowerShell进程 ===")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 等待一下
    import time
    time.sleep(2)
    
    # 重新连接确认
    ssh2 = paramiko.SSHClient()
    ssh2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh2.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    print("\n=== 确认进程状态 ===")
    stdin, stdout, stderr = ssh2.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    stdin, stdout, stderr = ssh2.exec_command('tasklist /FI "IMAGENAME eq powershell.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh2.close()
    print("\n所有watcher进程已停止")

if __name__ == "__main__":
    stop()
