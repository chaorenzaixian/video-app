#!/usr/bin/env python3
"""查看转码服务器上的watcher脚本"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 查看桌面上的脚本
    print("\n=== 桌面上的脚本文件 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-ChildItem C:\\Users\\Administrator\\Desktop\\*.ps1 | Select-Object Name, Length, LastWriteTime"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 查看watcher脚本最后50行
    print("\n=== D:\\VideoTranscode\\scripts\\watcher.ps1 最后80行 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 -Tail 80"')
    content = stdout.read().decode('utf-8', errors='replace')
    print(content)
    
    # 查看脚本总行数
    print("\n=== 脚本总行数 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "(Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1).Count"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
