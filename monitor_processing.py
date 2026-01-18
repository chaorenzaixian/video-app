#!/usr/bin/env python3
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("👀 监控文件处理")
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
    
    for i in range(4):
        print(f"📊 检查 {i+1}/4 ({time.strftime('%H:%M:%S')})")
        print("-" * 50)
        
        # Downloads/short
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
        count = stdout.read().decode('gbk', errors='ignore').strip()
        print(f"  Downloads/short: {count} 个文件")
        
        # Downloads/long
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\long\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
        count = stdout.read().decode('gbk', errors='ignore').strip()
        print(f"  Downloads/long: {count} 个文件")
        
        # Processing
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
        count = stdout.read().decode('gbk', errors='ignore').strip()
        print(f"  Processing: {count} 个文件")
        
        # Completed
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\*.mp4 /b /s 2>nul | find /C ".mp4"', timeout=30)
        count = stdout.read().decode('gbk', errors='ignore').strip()
        print(f"  Completed: {count} 个文件")
        
        # 最新日志
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 2"', timeout=30)
        log = stdout.read().decode('utf-8', errors='ignore').strip()
        if log:
            lines = log.split('\n')
            if len(lines) > 0:
                print(f"  日志: {lines[-1][:80]}")
        
        if i < 3:
            print("\n⏳ 等待15秒...\n")
            time.sleep(15)
    
    print("\n" + "=" * 50)
    print("📝 详细日志:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n'):
        print(f"  {line}")
    
    print("\n📝 转码日志:")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n'):
        print(f"  {line}")
    
except Exception as e:
    print(f"❌ 监控失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
