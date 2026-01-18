#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 快速检查")
print("=" * 50)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 {TRANSCODE_SERVER}...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!\n")
    
    # 1. Downloads 根目录
    print("📁 Downloads 根目录:")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  {files}")
    else:
        print("  (空)")
    
    # 2. Downloads/short
    print("\n📁 Downloads/short:")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  {files}")
    else:
        print("  (空)")
    
    # 3. Downloads/long
    print("\n📁 Downloads/long:")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\long\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  {files}")
    else:
        print("  (空)")
    
    # 4. Processing
    print("\n📁 Processing:")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  {files}")
    else:
        print("  (空)")
    
    # 5. Watcher 进程
    print("\n🔄 Watcher 进程:")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'powershell.exe' in output:
        lines = output.split('\n')
        print(f"  找到 {len(lines)} 个 PowerShell 进程")
    else:
        print("  ❌ 未找到 PowerShell 进程")
    
    # 6. 最新日志
    print("\n📝 Watcher 日志（最新5行）:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 -ErrorAction SilentlyContinue"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    if log:
        for line in log.split('\n')[:5]:
            print(f"  {line}")
    else:
        print("  (无日志)")
    
    # 7. 转码日志
    print("\n📝 转码日志（最新5行）:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 5 -ErrorAction SilentlyContinue"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    if log:
        for line in log.split('\n')[:5]:
            print(f"  {line}")
    else:
        print("  (无日志)")
    
    # 8. 检查第一个视频文件的详细信息
    print("\n🎬 检查视频文件详情:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "$f = Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File -Recurse | Select-Object -First 1; if ($f) { Write-Host $f.FullName; Write-Host \'Size:\' $f.Length; & ffprobe -v error -show_entries format=duration -of csv=p=0 $f.FullName 2>&1 } else { Write-Host \'No files\' }"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  {output}")
    
    print("\n" + "=" * 50)
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
