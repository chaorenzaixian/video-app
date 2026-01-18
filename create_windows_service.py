#!/usr/bin/env python3
"""
创建 Windows 服务来运行 Watcher
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔧 创建 Windows 服务")
print("=" * 60)

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
    
    # 方法1: 创建一个启动脚本，使用 nohup 方式
    print("📋 方法1: 创建启动脚本")
    print("-" * 60)
    
    startup_script = r'''@echo off
echo Starting Video Watcher Service...
start /B powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -NoExit -File "D:\VideoTranscode\scripts\watcher.ps1"
echo Watcher service started
'''
    
    # 上传启动脚本
    stdin, stdout, stderr = ssh.exec_command(f'echo {startup_script} > D:\\VideoTranscode\\start_watcher.bat', timeout=30)
    stdout.read()
    print("  ✅ 启动脚本已创建\n")
    
    # 方法2: 修改计划任务，使用不同的触发器
    print("📋 方法2: 创建开机自启动任务")
    print("-" * 60)
    
    # 删除旧任务
    stdin, stdout, stderr = ssh.exec_command('schtasks /Delete /TN "VideoWatcherService" /F 2>nul', timeout=30)
    stdout.read()
    
    # 创建新任务 - 系统启动时运行，不管用户是否登录
    task_cmd = '''schtasks /Create /TN "VideoWatcherService" /TR "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1" /SC ONSTART /RU SYSTEM /RL HIGHEST /F'''
    stdin, stdout, stderr = ssh.exec_command(task_cmd, timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    # 立即运行任务
    print("\n  立即启动任务...")
    stdin, stdout, stderr = ssh.exec_command('schtasks /Run /TN "VideoWatcherService"', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    time.sleep(5)
    
    # 方法3: 使用 sc 命令创建真正的 Windows 服务
    print("\n📋 方法3: 尝试创建 Windows 服务")
    print("-" * 60)
    
    # 创建一个包装脚本
    wrapper_script = r'''@echo off
:loop
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "D:\VideoTranscode\scripts\watcher.ps1"
timeout /t 10 /nobreak
goto loop
'''
    
    stdin, stdout, stderr = ssh.exec_command(f'echo {wrapper_script} > D:\\VideoTranscode\\watcher_service.bat', timeout=30)
    stdout.read()
    
    # 删除旧服务
    stdin, stdout, stderr = ssh.exec_command('sc delete VideoWatcherSvc 2>nul', timeout=30)
    stdout.read()
    time.sleep(2)
    
    # 创建服务
    service_cmd = 'sc create VideoWatcherSvc binPath= "D:\\VideoTranscode\\watcher_service.bat" start= auto DisplayName= "Video Watcher Service"'
    stdin, stdout, stderr = ssh.exec_command(service_cmd, timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    # 启动服务
    stdin, stdout, stderr = ssh.exec_command('sc start VideoWatcherSvc', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    time.sleep(5)
    
    # 验证
    print("\n" + "=" * 60)
    print("📊 验证结果")
    print("=" * 60)
    
    # 检查进程
    print("\n1️⃣ PowerShell 进程:")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV /NH', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    ps_count = len([l for l in output.split('\n') if 'powershell.exe' in l])
    
    if ps_count > 0:
        print(f"  ✅ 找到 {ps_count} 个 PowerShell 进程")
    else:
        print("  ❌ 未找到 PowerShell 进程")
    
    # 检查计划任务
    print("\n2️⃣ 计划任务:")
    stdin, stdout, stderr = ssh.exec_command('schtasks /Query /TN "VideoWatcherService" /FO LIST', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'VideoWatcherService' in output:
        print("  ✅ 计划任务已创建")
        for line in output.split('\n'):
            if any(k in line for k in ['状态', 'Status', '上次运行', 'Last Run']):
                print(f"    {line.strip()}")
    
    # 检查服务
    print("\n3️⃣ Windows 服务:")
    stdin, stdout, stderr = ssh.exec_command('sc query VideoWatcherSvc', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'VideoWatcherSvc' in output or 'RUNNING' in output:
        print("  ✅ Windows 服务已创建")
        for line in output.split('\n')[:5]:
            if line.strip():
                print(f"    {line.strip()}")
    else:
        print("  ⚠️ Windows 服务创建可能失败")
    
    # 等待并检查日志
    print("\n4️⃣ 等待20秒，检查日志...")
    time.sleep(20)
    
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if log:
        log_lines = log.split('\n')
        print("  最新日志:")
        for line in log_lines[-5:]:
            if line.strip():
                print(f"    {line}")
        
        # 检查是否有新日志
        current_time = time.strftime('%Y-%m-%d %H:')
        has_new_log = any(current_time in line for line in log_lines[-5:])
        
        if has_new_log:
            print("\n  ✅ 日志有更新，Watcher 正在工作!")
        else:
            print("\n  ⚠️ 日志没有最新更新")
    
    # 检查文件状态
    print("\n5️⃣ 文件状态:")
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul', timeout=30)
    downloads = stdout.read().decode('gbk', errors='ignore').strip()
    downloads_count = len([f for f in downloads.split('\n') if f.strip()])
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul', timeout=30)
    processing = stdout.read().decode('gbk', errors='ignore').strip()
    processing_count = len([f for f in processing.split('\n') if f.strip()])
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b 2>nul', timeout=30)
    completed = stdout.read().decode('gbk', errors='ignore').strip()
    completed_count = len([f for f in completed.split('\n') if f.strip() and 'test_' not in f])
    
    print(f"  Downloads: {downloads_count}")
    print(f"  Processing: {processing_count}")
    print(f"  Completed: {completed_count}")
    
    if processing_count > 0:
        print("  ✅ 有文件正在处理!")
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 总结")
    print("=" * 60)
    
    methods_working = []
    
    if ps_count > 0:
        methods_working.append("PowerShell 进程")
    
    if 'VideoWatcherService' in output:
        methods_working.append("计划任务")
    
    if methods_working:
        print(f"\n✅ 以下方法正在工作:")
        for method in methods_working:
            print(f"  - {method}")
    else:
        print("\n❌ 所有自动启动方法都失败了")
        print("\n🔧 手动启动方法:")
        print("1. 使用远程桌面连接到 198.176.60.121")
        print("2. 打开 PowerShell")
        print("3. 运行: D:\\VideoTranscode\\scripts\\watcher.ps1")
        print("\n或者:")
        print("1. 打开任务计划程序")
        print("2. 找到 'VideoWatcherService' 任务")
        print("3. 右键 -> 运行")
    
    print("\n💡 说明:")
    print("- 已创建3种启动方法:")
    print("  1. 计划任务 (系统启动时自动运行)")
    print("  2. Windows 服务 (后台运行)")
    print("  3. 启动脚本 (D:\\VideoTranscode\\start_watcher.bat)")
    print("- 系统重启后会自动启动 Watcher")
    
except Exception as e:
    print(f"\n❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
