#!/usr/bin/env python3
"""检查转码进度"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查completed目录最新的
    print("=== Completed/long最新目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查ffmpeg进程
    print("\n=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查最新日志
    print("\n=== 最新日志(最后20行) ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 20"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查processing目录
    print("\n=== Processing目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\processing')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
