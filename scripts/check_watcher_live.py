#!/usr/bin/env python3
"""实时检查watcher状态"""
import paramiko
import time

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    print("等待watcher检测文件...")
    time.sleep(15)
    
    # 检查最新日志
    print("\n=== 最新日志 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 30"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查processing目录
    print("\n=== Processing目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查ffmpeg进程
    print("\n=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查downloads/long还有多少文件
    print("\n=== Downloads/long剩余文件 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\downloads\\long\\*.mp4')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "无MP4文件（都在处理中）")
    
    ssh.close()

if __name__ == "__main__":
    check()
