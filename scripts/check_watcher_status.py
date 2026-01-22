#!/usr/bin/env python3
"""检查watcher状态"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查ffmpeg进程
    print("\n=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist | findstr ffmpeg')
    print(stdout.read().decode('utf-8', errors='replace') or "无ffmpeg进程")
    
    # 检查PowerShell进程
    print("\n=== PowerShell进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist | findstr powershell')
    print(stdout.read().decode('utf-8', errors='replace') or "无PowerShell进程")
    
    # 检查processing目录
    print("\n=== Processing目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\processing')
    print(stdout.read().decode('utf-8', errors='replace') or "空")
    
    # 检查downloads目录
    print("\n=== Downloads\\long目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\downloads\\long')
    print(stdout.read().decode('utf-8', errors='replace') or "空")
    
    print("\n=== Downloads\\short目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\downloads\\short')
    print(stdout.read().decode('utf-8', errors='replace') or "空")
    
    # 最新日志
    print("\n=== 最新日志(最后30行) ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 30"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
