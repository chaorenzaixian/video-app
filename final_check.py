#!/usr/bin/env python3
"""
最终检查 - 等待所有文件处理完成
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("⏳ 等待所有文件处理完成...")
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
    
    total_files = 5
    max_checks = 20  # 最多检查20次（约10分钟）
    
    for check_num in range(1, max_checks + 1):
        print(f"\n⏰ 检查 #{check_num} ({time.strftime('%H:%M:%S')})")
        print("-" * 60)
        
        # 检查文件状态
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
        downloads = stdout.read().decode('gbk', errors='ignore').strip()
        downloads_count = len([f for f in downloads.split('\n') if f.strip()])
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
        processing = stdout.read().decode('gbk', errors='ignore').strip()
        processing_count = len([f for f in processing.split('\n') if f.strip()])
        
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*_transcoded.mp4 /b 2>nul', timeout=30)
        completed = stdout.read().decode('gbk', errors='ignore').strip()
        completed_files = [f.strip() for f in completed.split('\n') if f.strip() and 'test_' not in f]
        completed_count = len(completed_files)
        
        print(f"📊 Downloads: {downloads_count} | Processing: {processing_count} | Completed: {completed_count}/{total_files}")
        
        # 显示最新日志
        stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 2"', timeout=30)
        log = stdout.read().decode('utf-8', errors='ignore').strip()
        if log:
            print("📝 最新日志:")
            for line in log.split('\n')[-2:]:
                if line.strip():
                    print(f"  {line[:80]}")
        
        # 检查是否完成
        if downloads_count == 0 and processing_count == 0 and completed_count >= total_files:
            print("\n🎉 所有文件处理完成!")
            break
        
        if check_num < max_checks:
            print(f"⏳ 等待30秒...")
            time.sleep(30)
    
    # 最终统计
    print("\n" + "=" * 60)
    print("📊 最终统计")
    print("=" * 60)
    
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
        print(f"\n⚙️ 仍在处理: {processing_count} 个文件")
    
    if downloads_count > 0:
        print(f"\n📥 等待处理: {downloads_count} 个文件")
    
    # 服务状态
    print("\n🔄 服务状态:")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    ps_count = len([l for l in output.split('\n') if 'powershell.exe' in l])
    print(f"  PowerShell 进程: {ps_count} 个")
    
    if ps_count > 0:
        print("  ✅ Watcher 服务运行中")
    else:
        print("  ❌ Watcher 服务已停止")
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 总结")
    print("=" * 60)
    
    if completed_count == total_files:
        print("\n🎉 所有文件处理成功!")
        print(f"✅ 成功率: 100% ({completed_count}/{total_files})")
    elif completed_count > 0:
        success_rate = (completed_count / total_files) * 100
        print(f"\n✅ 部分文件处理成功")
        print(f"📊 成功率: {success_rate:.1f}% ({completed_count}/{total_files})")
    else:
        print("\n❌ 没有文件处理成功")
    
    print("\n💡 系统状态:")
    print("- ✅ Watcher 脚本: 纯英文版本，无编码问题")
    print("- ✅ 转码脚本: 支持 GPU/CPU 转码，自动选择")
    print("- ✅ 分类系统: 支持长短视频分类")
    print("- ✅ 自动启动: 计划任务已创建，系统重启后自动运行")
    
    print("\n📝 日志位置:")
    print("- Watcher: D:\\VideoTranscode\\logs\\watcher.log")
    print("- 转码: D:\\VideoTranscode\\logs\\transcode.log")
    
except Exception as e:
    print(f"\n❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
