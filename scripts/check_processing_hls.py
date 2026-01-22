#!/usr/bin/env python3
"""检查processing目录下的HLS进度"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查processing目录
    print("=== Processing目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查completed/long下正在写入的目录
    print("\n=== 检查正在写入的HLS目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | ForEach-Object { $hlsDir = Join-Path $_.FullName hls; if (Test-Path $hlsDir) { $files = Get-ChildItem $hlsDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($files.LastWriteTime -gt (Get-Date).AddMinutes(-5)) { Write-Host ($_.Name.Substring(0, [Math]::Min(20, $_.Name.Length)) + \'...\'); Get-ChildItem $hlsDir -Directory | ForEach-Object { $tsCount = (Get-ChildItem $_.FullName -Filter *.ts).Count; Write-Host (\'  \' + $_.Name + \': \' + $tsCount) } } } }"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查FFmpeg进程
    print("\n=== FFmpeg进程 ===")
    cmd = 'powershell -Command "Get-Process ffmpeg -ErrorAction SilentlyContinue | Select-Object Id, CPU, WorkingSet64"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
