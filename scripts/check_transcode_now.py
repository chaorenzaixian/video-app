#!/usr/bin/env python3
"""检查当前转码状态"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查最新completed目录
    print("\n=== 最新completed目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object { $_.Name }"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查最新目录的内容
    print("\n=== 最新目录内容 ===")
    cmd = 'powershell -Command "$d = (Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; Get-ChildItem $d -Recurse | Select-Object Name, Length"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查downloads/long是否有mp4
    print("\n=== Downloads/long中的MP4文件 ===")
    cmd = 'dir /B D:\\VideoTranscode\\downloads\\long\\*.mp4'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "无MP4文件")
    
    # 检查watcher日志最后50行
    print("\n=== Watcher日志最后50行 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
