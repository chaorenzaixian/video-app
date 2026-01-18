#!/usr/bin/env python3
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔄 重置并重新处理视频文件")
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
    
    # 1. 停止 watcher
    print("📋 停止 watcher...")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
    stdout.read()
    print("  ✅ 已停止")
    
    time.sleep(3)
    
    # 2. 移动文件回 downloads/short
    print("\n📋 将文件移回 downloads/short...")
    stdin, stdout, stderr = ssh.exec_command('move D:\\VideoTranscode\\processing\\*.mp4 D:\\VideoTranscode\\downloads\\short\\ 2>nul', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    # 3. 检查文件
    print("\n📋 检查 downloads/short 目录...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        file_list = files.split('\n')
        print(f"  找到 {len(file_list)} 个文件:")
        for f in file_list[:10]:
            print(f"    - {f}")
    else:
        print("  (空)")
    
    # 4. 启动 watcher
    print("\n📋 启动 watcher...")
    stdin, stdout, stderr = ssh.exec_command('start /min powershell -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)
    stdout.read()
    print("  ✅ 已启动")
    
    time.sleep(5)
    
    # 5. 监控处理过程
    print("\n⏳ 监控处理过程（每15秒检查一次）...")
    for i in range(6):  # 监控90秒
        time.sleep(15)
        
        print(f"\n📊 检查 {i+1}/6 ({time.strftime('%H:%M:%S')})")
        
        # 检查各目录文件数
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
        downloads_count = stdout.read().decode('gbk', errors='ignore').strip()
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
        processing_count = stdout.read().decode('gbk', errors='ignore').strip()
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\*_transcoded.mp4 /b /s 2>nul | find /C ".mp4"', timeout=30)
        completed_count = stdout.read().decode('gbk', errors='ignore').strip()
        
        print(f"  Downloads/short: {downloads_count} | Processing: {processing_count} | Completed: {completed_count}")
        
        # 查看最新日志
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 2"', timeout=30)
        log = stdout.read().decode('utf-8', errors='ignore').strip()
        if log:
            lines = log.split('\n')
            if len(lines) > 0:
                print(f"  日志: {lines[-1][:80]}")
    
    print("\n" + "=" * 50)
    print("📊 最终状态")
    print("=" * 50)
    
    # 最终检查
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
    downloads = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"\nDownloads/short: {len(downloads.split()) if downloads else 0} 个文件")
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
    processing = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"Processing: {len(processing.split()) if processing else 0} 个文件")
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\*_transcoded.mp4 /b /s 2>nul', timeout=30)
    completed = stdout.read().decode('gbk', errors='ignore').strip()
    if completed:
        print(f"Completed: {len(completed.split())} 个转码文件")
        print("\n最新转码的文件:")
        for f in completed.split('\n')[-5:]:
            print(f"  - {f}")
    else:
        print("Completed: 0 个转码文件")
    
    # 查看转码日志
    print("\n📝 最新转码日志:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n')[:10]:
        print(f"  {line}")
    
except Exception as e:
    print(f"❌ 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
