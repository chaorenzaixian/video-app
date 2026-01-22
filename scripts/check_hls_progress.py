#!/usr/bin/env python3
"""检查HLS转码进度"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查正在处理的视频的HLS进度
    videos = [
        ("公交车上的激情暴露狂", 6569, 720),  # 109分钟, 720p
        ("失足学妹", 2362, 1080),  # 39分钟, 1080p
    ]
    
    for name, duration, height in videos:
        expected_segments = int(duration / 10) + 1  # 10秒一个分片
        print(f"\n=== {name} (预计{expected_segments}个分片) ===")
        
        # 检查completed目录下的HLS
        cmd = f'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Where-Object {{ $_.Name -like \'*{name[:4]}*\' }} | ForEach-Object {{ $hlsDir = Join-Path $_.FullName \'hls\'; if (Test-Path $hlsDir) {{ Get-ChildItem $hlsDir -Directory | ForEach-Object {{ $tsCount = (Get-ChildItem $_.FullName -Filter *.ts).Count; Write-Host \\\"$($_.Name): $tsCount segments\\\" }} }} }}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='replace')
        print(output if output.strip() else "  (尚未开始生成HLS)")
    
    # 检查ffmpeg进程数
    print("\n=== FFmpeg进程 ===")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe" | find /c "ffmpeg"')
    count = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"  运行中的FFmpeg进程: {count}")
    
    # 检查最新日志
    print("\n=== 最新日志 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 10"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    ssh.close()

if __name__ == "__main__":
    check()
