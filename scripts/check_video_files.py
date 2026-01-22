#!/usr/bin/env python3
"""检查视频文件完整性"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 获取最新5个目录
    print("=== 获取最新目录 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 5 FullName"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    
    # 解析目录路径
    lines = [l.strip() for l in output.split('\n') if 'D:\\' in l]
    
    for dir_path in lines:
        dir_path = dir_path.strip()
        if not dir_path:
            continue
            
        # 获取目录名
        dir_name = dir_path.split('\\')[-1]
        short_name = dir_name[:30] + '...' if len(dir_name) > 30 else dir_name
        
        print(f"\n{'='*50}")
        print(f"目录: {short_name}")
        print('='*50)
        
        # 检查master.m3u8
        cmd = f'if exist "{dir_path}\\hls\\master.m3u8" (echo [OK] master.m3u8) else (echo [ERROR] master.m3u8 NOT found)'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
        
        # 检查各分辨率的ts数量
        cmd = f'powershell -Command "Get-ChildItem \'{dir_path}\\hls\' -Directory -ErrorAction SilentlyContinue | ForEach-Object {{ $c = (Get-ChildItem $_.FullName -Filter *.ts).Count; Write-Host (\'  \' + $_.Name + \': \' + $c + \' segments\') }}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
        
        # 检查封面数量
        cmd = f'powershell -Command "$c = (Get-ChildItem \'{dir_path}\\covers\' -Filter *.webp -ErrorAction SilentlyContinue).Count; Write-Host (\'  Covers: \' + $c + \' webp files\')"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
        
        # 检查预览视频
        cmd = f'powershell -Command "$p = Get-ChildItem \'{dir_path}\' -Filter *_preview.webm -ErrorAction SilentlyContinue; if ($p) {{ Write-Host (\'  Preview: \' + $p.Name + \' (\' + [math]::Round($p.Length/1MB, 2) + \' MB)\') }} else {{ Write-Host \'  [WARNING] Preview NOT found\' }}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
    
    # 检查当前转码状态
    print(f"\n{'='*50}")
    print("当前转码状态")
    print('='*50)
    
    # FFmpeg进程
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq ffmpeg.exe" | find /c "ffmpeg"')
    ffmpeg_count = stdout.read().decode().strip()
    print(f"FFmpeg进程数: {ffmpeg_count}")
    
    # Processing目录
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\processing\\*.mp4 2>nul')
    processing = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"Processing中的视频: {processing if processing else '无'}")
    
    # Downloads目录
    stdin, stdout, stderr = ssh.exec_command('dir /B D:\\VideoTranscode\\downloads\\long\\*.mp4 2>nul')
    downloads = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"等待处理的视频: {downloads if downloads else '无'}")
    
    ssh.close()

if __name__ == "__main__":
    check()
