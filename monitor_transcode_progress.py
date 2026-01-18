#!/usr/bin/env python3
"""
监控转码进度
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("📊 监控转码进度")
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
    
    for i in range(6):  # 监控6次，每次30秒
        print(f"\n⏰ 检查 #{i+1} ({time.strftime('%H:%M:%S')})")
        print("-" * 60)
        
        # 1. 文件状态
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
        downloads = stdout.read().decode('gbk', errors='ignore').strip()
        downloads_count = len([f for f in downloads.split('\n') if f.strip()])
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
        processing = stdout.read().decode('gbk', errors='ignore').strip()
        processing_files = [f.strip() for f in processing.split('\n') if f.strip()]
        processing_count = len(processing_files)
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b 2>nul', timeout=30)
        completed = stdout.read().decode('gbk', errors='ignore').strip()
        completed_files = [f.strip() for f in completed.split('\n') if f.strip()]
        completed_count = len(completed_files)
        
        print(f"📁 Downloads: {downloads_count} | Processing: {processing_count} | Completed: {completed_count}")
        
        if processing_files:
            print(f"  ⚙️ 正在处理: {', '.join(processing_files[:3])}")
        
        if completed_files:
            print(f"  ✅ 已完成: {', '.join(completed_files[:3])}")
        
        # 2. 最新日志
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3"', timeout=30)
        log = stdout.read().decode('utf-8', errors='ignore').strip()
        if log:
            print("  📝 最新日志:")
            for line in log.split('\n')[-3:]:
                if line.strip():
                    print(f"    {line[:80]}")
        
        # 3. 转码日志
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 2"', timeout=30)
        transcode_log = stdout.read().decode('utf-8', errors='ignore').strip()
        if transcode_log:
            print("  🎬 转码日志:")
            for line in transcode_log.split('\n')[-2:]:
                if line.strip():
                    print(f"    {line[:80]}")
        
        # 检查是否完成
        if downloads_count == 0 and processing_count == 0 and completed_count > 0:
            print("\n🎉 所有文件处理完成!")
            break
        
        if i < 5:  # 不是最后一次
            print(f"\n  ⏳ 等待30秒...")
            time.sleep(30)
    
    # 最终统计
    print("\n" + "=" * 60)
    print("📊 最终统计")
    print("=" * 60)
    
    # 详细的完成文件列表
    if completed_count > 0:
        print(f"\n✅ 已完成 {completed_count} 个文件:")
        for f in completed_files:
            # 获取文件大小
            stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\short\\{f}\').Length / 1MB"', timeout=30)
            size = stdout.read().decode('utf-8', errors='ignore').strip()
            try:
                size_mb = float(size)
                print(f"  📹 {f} ({size_mb:.1f} MB)")
            except:
                print(f"  📹 {f}")
    
    if processing_count > 0:
        print(f"\n⚙️ 仍在处理 {processing_count} 个文件:")
        for f in processing_files:
            print(f"  ⏳ {f}")
    
    if downloads_count > 0:
        print(f"\n📥 等待处理 {downloads_count} 个文件")
    
    # PowerShell 进程状态
    print("\n🔄 服务状态:")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    ps_count = len([l for l in output.split('\n') if 'powershell.exe' in l])
    print(f"  PowerShell 进程: {ps_count} 个")
    
    if ps_count > 0:
        print("  ✅ Watcher 服务运行中")
    else:
        print("  ❌ Watcher 服务已停止")
    
except Exception as e:
    print(f"\n❌ 监控失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
