#!/usr/bin/env python3
"""检查watcher实例"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查PowerShell进程
    print("=== PowerShell进程 ===")
    cmd = 'powershell -Command "Get-Process powershell | Select-Object Id, StartTime"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查watcher.lock文件
    print("\n=== Watcher Lock文件 ===")
    stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\watcher.lock')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查Guardian任务状态
    print("\n=== Guardian计划任务 ===")
    stdin, stdout, stderr = ssh.exec_command('schtasks /query /tn WatcherGuardian')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查FFmpeg进程
    print("\n=== FFmpeg进程 ===")
    cmd = 'powershell -Command "Get-Process ffmpeg -ErrorAction SilentlyContinue | Select-Object Id, StartTime, CPU"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
