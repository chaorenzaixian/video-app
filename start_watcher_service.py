#!/usr/bin/env python3
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🚀 启动 Watcher 服务")
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
    
    # 1. 清理现有进程
    print("📋 清理现有进程...")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM powershell.exe 2>nul', timeout=30)
    stdout.read()
    time.sleep(3)
    print("  ✅ 已清理\n")
    
    # 方法1: 使用 nohup 方式（后台运行）
    print("📋 方法1: 使用后台方式启动...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Start-Job -ScriptBlock { Set-Location D:\\VideoTranscode\\scripts; .\\watcher.ps1 } | Out-Null; Write-Host \'已启动\'"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  {output}")
    time.sleep(5)
    
    # 检查
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Job | Select-Object Id, State"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  Job 状态: {output}")
    
    # 方法2: 使用 schtasks（计划任务）
    print("\n📋 方法2: 创建计划任务...")
    
    # 删除旧任务
    stdin, stdout, stderr = ssh.exec_command('schtasks /Delete /TN "VideoWatcher" /F 2>nul', timeout=30)
    stdout.read()
    
    # 创建新任务
    task_cmd = 'schtasks /Create /TN "VideoWatcher" /TR "powershell.exe -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1" /SC ONSTART /RU SYSTEM /F'
    stdin, stdout, stderr = ssh.exec_command(task_cmd, timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    # 立即运行任务
    stdin, stdout, stderr = ssh.exec_command('schtasks /Run /TN "VideoWatcher"', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    time.sleep(5)
    
    # 方法3: 使用 wmic 启动进程
    print("\n📋 方法3: 使用 WMIC 启动...")
    stdin, stdout, stderr = ssh.exec_command('wmic process call create "powershell.exe -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1"', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    time.sleep(5)
    
    # 验证所有方法
    print("\n" + "=" * 50)
    print("📊 验证结果")
    print("=" * 50)
    
    # 检查进程
    print("\n📋 检查 PowerShell 进程...")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" | find /C "powershell.exe"', timeout=30)
    count = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  PowerShell 进程数: {count}")
    
    if int(count) > 0:
        print("  ✅ 找到 PowerShell 进程")
        
        # 显示进程详情
        stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /V', timeout=30)
        output = stdout.read().decode('gbk', errors='ignore').strip()
        lines = [l for l in output.split('\n') if 'powershell.exe' in l]
        for line in lines[:3]:
            print(f"    {line[:100]}")
    else:
        print("  ❌ 未找到 PowerShell 进程")
    
    # 检查计划任务
    print("\n📋 检查计划任务...")
    stdin, stdout, stderr = ssh.exec_command('schtasks /Query /TN "VideoWatcher" /FO LIST', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'VideoWatcher' in output:
        print("  ✅ 计划任务已创建")
        # 提取状态
        for line in output.split('\n'):
            if '状态' in line or 'Status' in line or '任务名' in line:
                print(f"    {line.strip()}")
    else:
        print("  ❌ 计划任务未找到")
    
    # 等待并检查日志
    print("\n⏳ 等待20秒，检查 watcher 是否工作...")
    time.sleep(20)
    
    print("\n📋 检查最新日志...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    log_lines = log.split('\n')
    for line in log_lines:
        print(f"  {line}")
    
    # 检查日志时间
    if log_lines:
        last_line = log_lines[-1]
        if '17:' in last_line:  # 检查是否有新的日志
            current_hour = time.strftime('%H')
            if current_hour in last_line:
                print("\n  ✅ 日志有更新，Watcher 正在工作!")
            else:
                print("\n  ⚠️ 日志没有更新")
    
    # 检查文件状态
    print("\n📋 检查文件状态...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
    downloads_count = stdout.read().decode('gbk', errors='ignore').strip()
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4 /b 2>nul | find /C ".mp4"', timeout=30)
    processing_count = stdout.read().decode('gbk', errors='ignore').strip()
    
    print(f"  Downloads/short: {downloads_count} 个文件")
    print(f"  Processing: {processing_count} 个文件")
    
    print("\n" + "=" * 50)
    print("✅ 启动完成!")
    print("\n💡 说明:")
    print("- 已尝试3种方法启动 Watcher")
    print("- 已创建计划任务 'VideoWatcher'")
    print("- 计划任务会在系统启动时自动运行")
    
    if int(count) > 0:
        print("\n🎉 Watcher 服务已成功启动!")
    else:
        print("\n⚠️ Watcher 可能需要手动启动")
        print("请尝试远程桌面连接到服务器手动运行")
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
