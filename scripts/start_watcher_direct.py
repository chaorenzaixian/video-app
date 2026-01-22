#!/usr/bin/env python3
"""直接启动watcher"""
import paramiko
import time

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def start():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 使用wmic启动进程
    print("\n=== 启动Watcher (wmic方式) ===")
    cmd = 'wmic process call create "powershell.exe -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    time.sleep(5)
    
    # 验证
    print("\n=== 验证进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查ffmpeg
    print("\n=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查日志
    print("\n=== 最新日志 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 15"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    start()
