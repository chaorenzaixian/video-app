#!/usr/bin/env python3
"""检查视频MP4文件位置"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查watcher进程
    print("=== PowerShell进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 搜索所有mp4文件
    print("\n=== 所有MP4文件 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /S /B D:\\VideoTranscode\\*.mp4')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "无MP4文件")
    
    # 检查failed目录
    print("\n=== Failed目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\failed')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "空或不存在")
    
    # 检查processing目录
    print("\n=== Processing目录 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\processing')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "空")
    
    # 检查那个视频的HLS是否完整
    print("\n=== 检查HLS完整性 ===")
    cmd = '''powershell -Command "$d = (Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName; $m3u8 = Get-Content (Join-Path $d 'hls\\1080p\\playlist.m3u8'); $segCount = ($m3u8 | Select-String -Pattern 'seg_').Count; Write-Host 'Segments in playlist: ' $segCount; $tsCount = (Get-ChildItem (Join-Path $d 'hls\\1080p') -Filter '*.ts').Count; Write-Host 'TS files: ' $tsCount"'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
