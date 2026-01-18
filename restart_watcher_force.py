#!/usr/bin/env python3
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔄 强制重启 Watcher")
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
    
    # 1. 强制停止所有 PowerShell
    print("📋 停止所有 PowerShell 进程...")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    time.sleep(3)
    
    # 2. 检查脚本
    print("\n📋 检查 watcher 脚本...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\scripts\\watcher.ps1', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'watcher.ps1' in output:
        print("  ✅ 脚本存在")
    else:
        print("  ❌ 脚本不存在")
    
    # 3. 启动 watcher（使用不同的方法）
    print("\n📋 启动 watcher...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Start-Process powershell -ArgumentList \\\"-ExecutionPolicy Bypass -NoExit -File D:\\\\VideoTranscode\\\\scripts\\\\watcher.ps1\\\" -WindowStyle Minimized"', timeout=30)
    time.sleep(5)
    
    # 4. 验证进程
    print("\n📋 验证进程...")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe"', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'powershell.exe' in output:
        lines = [l for l in output.split('\n') if 'powershell.exe' in l]
        print(f"  ✅ 找到 {len(lines)} 个 PowerShell 进程")
    else:
        print("  ❌ 未找到 PowerShell 进程")
    
    # 5. 等待并检查日志
    print("\n⏳ 等待15秒，检查 watcher 是否工作...")
    time.sleep(15)
    
    print("\n📋 检查最新日志...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n'):
        print(f"  {line}")
    
    # 6. 检查文件状态
    print("\n📋 检查文件状态...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  Downloads/short: {len(files.split())} 个文件")
        for f in files.split('\n')[:3]:
            print(f"    - {f}")
    else:
        print("  Downloads/short: (空)")
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    if files:
        print(f"  Processing: {len(files.split())} 个文件")
    else:
        print("  Processing: (空)")
    
    print("\n" + "=" * 50)
    print("✅ 重启完成")
    print("\n💡 如果文件还没有被处理，可能的原因:")
    print("1. 视频文件格式有问题（不是真正的 MP4）")
    print("2. 文件大小 < 1000 字节")
    print("3. Watcher 脚本有问题")
    print("4. 文件名包含特殊字符")
    
except Exception as e:
    print(f"❌ 重启失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
