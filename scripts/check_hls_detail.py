#!/usr/bin/env python3
"""检查HLS详细进度"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查completed/long下最新目录
    print("=== Completed/long最新4个目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 4 Name"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查每个目录的HLS分片数
    print("=== HLS分片统计 ===")
    cmd = """powershell -Command "$dirs = Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 4; foreach ($d in $dirs) { $name = $d.Name.Substring(0, [Math]::Min(15, $d.Name.Length)); $hlsDir = Join-Path $d.FullName hls; if (Test-Path $hlsDir) { $total = (Get-ChildItem $hlsDir -Recurse -Filter *.ts).Count; Write-Host ($name + ': ' + $total + ' ts files') } else { Write-Host ($name + ': no hls dir') } }" """
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 检查ffmpeg进程
    print("=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
