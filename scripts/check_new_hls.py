#!/usr/bin/env python3
"""检查新生成的HLS文件"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查所有completed/long目录
    print("=== 所有Completed/long目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /AD /B D:\\VideoTranscode\\completed\\long')
    dirs = stdout.read().decode('utf-8', errors='replace').strip().split('\n')
    print(f"共 {len(dirs)} 个目录")
    
    # 检查最近修改的目录
    print("\n=== 最近修改的目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 6 Name, LastWriteTime"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查"失足学妹"目录的HLS
    print("=== 失足学妹目录HLS ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Where-Object { $_.Name -like \'*失*\' -or $_.Name -like \'*ʧ*\' } | ForEach-Object { $hlsDir = Join-Path $_.FullName hls; Get-ChildItem $hlsDir -Directory | ForEach-Object { $tsCount = (Get-ChildItem $_.FullName -Filter *.ts).Count; Write-Host ($_.Name + \': \' + $tsCount) } }"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查"公交车"目录的HLS
    print("=== 公交车目录HLS ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Where-Object { $_.Name -like \'*公*\' -or $_.Name -like \'*��*\' } | ForEach-Object { $hlsDir = Join-Path $_.FullName hls; Get-ChildItem $hlsDir -Directory | ForEach-Object { $tsCount = (Get-ChildItem $_.FullName -Filter *.ts).Count; Write-Host ($_.Name + \': \' + $tsCount) } }"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
