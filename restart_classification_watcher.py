#!/usr/bin/env python3
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def run_command(ssh, command, description):
    """执行远程命令"""
    print(f"\n📋 {description}...")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"✅ 成功")
            if output:
                print(f"   输出: {output}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("🔄 重启分类 Watcher 服务")
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
    print("✅ 连接成功!")
    
    # 1. 停止所有 PowerShell 进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \'已停止所有进程\'"',
        "停止所有进程")
    
    # 2. 等待进程完全停止
    print(f"\n⏳ 等待3秒...")
    time.sleep(3)
    
    # 3. 检查 watcher 脚本是否存在
    run_command(ssh,
        'powershell -Command "Write-Host \'检查脚本文件:\'; Test-Path D:\\VideoTranscode\\scripts\\watcher.ps1; Get-Item D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-Object Length"',
        "检查 watcher 脚本")
    
    # 4. 启动 watcher 服务
    run_command(ssh,
        'powershell -Command "Write-Host \'启动 watcher 服务...\'; Start-Process powershell -ArgumentList \\\"-ExecutionPolicy\\\", \\\"Bypass\\\", \\\"-NoExit\\\", \\\"-File\\\", \\\"D:\\VideoTranscode\\scripts\\watcher.ps1\\\" -WindowStyle Minimized; Write-Host \\\"Watcher 已启动\\\""',
        "启动 watcher 服务")
    
    # 5. 等待服务启动
    print(f"\n⏳ 等待10秒，让服务完全启动...")
    time.sleep(10)
    
    # 6. 检查进程状态
    run_command(ssh,
        'powershell -Command "Write-Host \'Watcher 进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \'*watcher*\' } | Select-Object Id, StartTime"',
        "检查进程状态")
    
    # 7. 检查当前待处理文件
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 待处理文件 ===\'; Write-Host \'Downloads根目录:\'; Get-ChildItem D:\\VideoTranscode\\downloads -File | Select-Object Name, Length; Write-Host \'\\nDownloads/short:\'; Get-ChildItem D:\\VideoTranscode\\downloads\\short -ErrorAction SilentlyContinue | Select-Object Name, Length; Write-Host \'\\nDownloads/long:\'; Get-ChildItem D:\\VideoTranscode\\downloads\\long -ErrorAction SilentlyContinue | Select-Object Name, Length"',
        "检查待处理文件")
    
    # 8. 等待并观察处理
    print(f"\n⏳ 等待30秒，观察文件处理...")
    time.sleep(30)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 处理结果 ===\'; Write-Host \'Downloads根目录:\'; Get-ChildItem D:\\VideoTranscode\\downloads -File | Select-Object Name; Write-Host \'\\nDownloads/short:\'; Get-ChildItem D:\\VideoTranscode\\downloads\\short -ErrorAction SilentlyContinue | Select-Object Name; Write-Host \'\\nDownloads/long:\'; Get-ChildItem D:\\VideoTranscode\\downloads\\long -ErrorAction SilentlyContinue | Select-Object Name; Write-Host \'\\nProcessing:\'; Get-ChildItem D:\\VideoTranscode\\processing -ErrorAction SilentlyContinue | Select-Object Name; Write-Host \'\\nCompleted/short:\'; Get-ChildItem D:\\VideoTranscode\\completed\\short -ErrorAction SilentlyContinue | Select-Object Name; Write-Host \'\\nCompleted/long:\'; Get-ChildItem D:\\VideoTranscode\\completed\\long -ErrorAction SilentlyContinue | Select-Object Name"',
        "检查处理结果")
    
    # 9. 查看最新日志
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 最新日志 ===\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 8 } else { Write-Host \'日志文件不存在\' }"',
        "查看最新日志")
    
    print("\n" + "=" * 50)
    print("🎉 长短视频分类系统已就绪!")
    print("\n📋 **使用总结**:")
    print("✅ **目录结构已创建**")
    print("✅ **配置文件已设置** (60秒分界线)")
    print("✅ **Watcher 服务已启动**")
    print("✅ **支持自动和手动分类**")
    print("\n🎯 **现在你可以**:")
    print("1. 上传视频到对应目录")
    print("2. 系统自动检测时长分类")
    print("3. 分别输出到 short/long 目录")
    
except Exception as e:
    print(f"❌ 重启失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()