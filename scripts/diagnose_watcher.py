#!/usr/bin/env python3
"""诊断watcher状态"""
import paramiko
from datetime import datetime

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def diagnose():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 获取服务器当前时间
    print("=== 服务器时间 ===")
    stdin, stdout, stderr = ssh.exec_command('echo %date% %time%')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查日志文件最后修改时间
    print("=== 日志文件状态 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 Name, LastWriteTime, Length"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查PowerShell进程
    print("=== PowerShell进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /V')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查FFmpeg进程CPU使用
    print("=== FFmpeg进程详情 ===")
    cmd = 'powershell -Command "Get-Process ffmpeg -ErrorAction SilentlyContinue | Select-Object Id, CPU, WorkingSet64, StartTime"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查completed目录最新文件的修改时间
    print("=== Completed目录最新文件 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    diagnose()
