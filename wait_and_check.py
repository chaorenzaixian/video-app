#!/usr/bin/env python3
"""
等待并检查转码结果
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("⏳ 等待转码完成...")
print("=" * 60)

# 先等待2分钟
print("等待2分钟让系统处理文件...")
for i in range(12):
    print(f"  {i*10}秒...", end='\r')
    time.sleep(10)

print("\n\n📊 检查结果")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    
    # 1. 文件状态
    print("\n📁 文件状态:")
    print("-" * 60)
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
    downloads = stdout.read().decode('gbk', errors='ignore').strip()
    downloads_files = [f.strip() for f in downloads.split('\n') if f.strip()]
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
    processing = stdout.read().decode('gbk', errors='ignore').strip()
    processing_files = [f.strip() for f in processing.split('\n') if f.strip()]
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b 2>nul', timeout=30)
    completed = stdout.read().decode('gbk', errors='ignore').strip()
    completed_files = [f.strip() for f in completed.split('\n') if f.strip()]
    
    print(f"  Downloads: {len(downloads_files)} 个")
    print(f"  Processing: {len(processing_files)} 个")
    print(f"  Completed: {len(completed_files)} 个")
    
    if downloads_files:
        print("\n  📥 等待处理:")
        for f in downloads_files:
            print(f"    - {f}")
    
    if processing_files:
        print("\n  ⚙️ 正在处理:")
        for f in processing_files:
            print(f"    - {f}")
    
    if completed_files:
        print("\n  ✅ 已完成:")
        for f in completed_files:
            # 获取文件大小
            stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\short\\{f}\').Length / 1MB"', timeout=30)
            size = stdout.read().decode('utf-8', errors='ignore').strip()
            try:
                size_mb = float(size)
                print(f"    - {f} ({size_mb:.1f} MB)")
            except:
                print(f"    - {f}")
    
    # 2. 最新日志
    print("\n📝 Watcher 日志（最新10行）:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n')[-10:]:
        if line.strip():
            print(f"  {line}")
    
    # 3. 转码日志
    print("\n📝 转码日志（最新10行）:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n')[-10:]:
        if line.strip():
            print(f"  {line}")
    
    # 4. 进程状态
    print("\n🔄 服务状态:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    ps_count = len([l for l in output.split('\n') if 'powershell.exe' in l])
    
    if ps_count > 0:
        print(f"  ✅ PowerShell 进程: {ps_count} 个 (Watcher 运行中)")
    else:
        print(f"  ❌ PowerShell 进程: 0 个 (Watcher 未运行)")
    
    # 5. 总结
    print("\n" + "=" * 60)
    print("📊 总结")
    print("=" * 60)
    
    total_files = 5
    completed_count = len(completed_files)
    processing_count = len(processing_files)
    waiting_count = len(downloads_files)
    
    if completed_count == total_files:
        print(f"\n🎉 所有文件处理完成! ({completed_count}/{total_files})")
    elif completed_count > 0:
        print(f"\n✅ 部分文件已完成: {completed_count}/{total_files}")
        print(f"⚙️ 正在处理: {processing_count}")
        print(f"📥 等待处理: {waiting_count}")
    else:
        print(f"\n⚠️ 还没有文件完成")
        print(f"⚙️ 正在处理: {processing_count}")
        print(f"📥 等待处理: {waiting_count}")
        
        if ps_count == 0:
            print("\n❌ Watcher 服务未运行!")
            print("请运行: python fix_and_start_watcher.py")
    
except Exception as e:
    print(f"\n❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
