#!/usr/bin/env python3
"""检查预览视频和封面生成情况"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查最近处理的视频目录
    videos = [
        "公交车上的激情暴露狂",
        "失足学妹",
        "深喉吞精山洞野战",
    ]
    
    print("=== 检查最近处理的视频 ===\n")
    
    # 获取所有completed/long目录
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Select-Object Name, FullName"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    dirs_output = stdout.read().decode('utf-8', errors='replace')
    
    # 检查每个目录的内容
    cmd = '''powershell -Command "
Get-ChildItem D:\\VideoTranscode\\completed\\long -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
    $dir = $_
    Write-Host '=========================================='
    Write-Host ('Directory: ' + $dir.Name.Substring(0, [Math]::Min(40, $dir.Name.Length)) + '...')
    Write-Host '=========================================='
    
    # 检查HLS
    $hlsDir = Join-Path $dir.FullName 'hls'
    if (Test-Path $hlsDir) {
        $masterM3u8 = Join-Path $hlsDir 'master.m3u8'
        if (Test-Path $masterM3u8) {
            Write-Host '  [OK] master.m3u8 exists'
        } else {
            Write-Host '  [ERROR] master.m3u8 NOT found'
        }
        $resolutions = Get-ChildItem $hlsDir -Directory
        foreach ($r in $resolutions) {
            $tsCount = (Get-ChildItem $r.FullName -Filter *.ts).Count
            $playlist = Join-Path $r.FullName 'playlist.m3u8'
            $playlistOk = Test-Path $playlist
            Write-Host ('  ' + $r.Name + ': ' + $tsCount + ' segments, playlist: ' + $playlistOk)
        }
    } else {
        Write-Host '  [ERROR] HLS directory NOT found'
    }
    
    # 检查封面
    $coversDir = Join-Path $dir.FullName 'covers'
    if (Test-Path $coversDir) {
        $coverCount = (Get-ChildItem $coversDir -Filter '*.webp').Count
        Write-Host ('  Covers: ' + $coverCount + ' webp files')
    } else {
        Write-Host '  [ERROR] Covers directory NOT found'
    }
    
    # 检查预览视频
    $previewFiles = Get-ChildItem $dir.FullName -Filter '*_preview.webm'
    if ($previewFiles.Count -gt 0) {
        foreach ($p in $previewFiles) {
            $sizeMB = [math]::Round($p.Length / 1MB, 2)
            Write-Host ('  Preview: ' + $p.Name + ' (' + $sizeMB + ' MB)')
        }
    } else {
        Write-Host '  [WARNING] Preview video NOT found'
    }
    
    Write-Host ''
}
"'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print(f"Errors: {err}")
    
    # 检查日志中的错误
    print("\n=== 检查日志中的错误 ===")
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\watcher_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content | Select-String -Pattern \'error|failed|Error|Failed\' | Select-Object -Last 10"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output if output.strip() else "  无错误记录")
    
    ssh.close()

if __name__ == "__main__":
    check()
