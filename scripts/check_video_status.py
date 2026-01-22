#!/usr/bin/env python3
"""检查特定视频的转码状态"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 搜索包含"山"的目录（那个视频名字里有"山"）
    print("\n=== 搜索completed目录中的相关视频 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-ChildItem -Path D:\\VideoTranscode\\completed\\long -Directory | Where-Object { $_.Name -like \'*山*\' } | Select-Object Name, LastWriteTime"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查该视频的HLS目录
    print("\n=== 检查HLS目录内容 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-ChildItem -Path \'D:\\VideoTranscode\\completed\\long\\*山*\\hls\' -Recurse -ErrorAction SilentlyContinue | Select-Object FullName | Format-Table -AutoSize"')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "(HLS目录不存在或为空)")
    
    # 检查日志中该视频的处理记录
    print("\n=== 日志中的处理记录 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher_20260120.log | Select-String -Pattern \'山\' | Select-Object -Last 20"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
