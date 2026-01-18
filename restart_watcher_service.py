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

print("🔄 重启 Watcher 服务")
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
    
    # 1. 检查当前 watcher 进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, ProcessName, StartTime"',
        "检查当前 watcher 进程")
    
    # 2. 强制停止所有 watcher 相关进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \\"已停止所有 watcher 进程\\""',
        "停止所有 watcher 进程")
    
    # 3. 等待进程完全停止
    print("\n⏳ 等待进程完全停止...")
    time.sleep(3)
    
    # 4. 确认没有 watcher 进程在运行
    run_command(ssh,
        'powershell -Command "if ((Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" }).Count -eq 0) { Write-Host \\"没有 watcher 进程在运行\\" } else { Write-Host \\"仍有 watcher 进程在运行\\" }"',
        "确认进程已停止")
    
    # 5. 检查 watcher.ps1 脚本是否存在
    run_command(ssh,
        'powershell -Command "if (Test-Path \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\") { Write-Host \\"watcher.ps1 脚本存在\\" } else { Write-Host \\"watcher.ps1 脚本不存在\\" }"',
        "检查 watcher 脚本")
    
    # 6. 启动新的 watcher 服务
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 服务已启动\\""',
        "启动新的 watcher 服务")
    
    # 7. 等待服务启动
    print("\n⏳ 等待服务启动...")
    time.sleep(5)
    
    # 8. 确认新进程已启动
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, ProcessName, StartTime"',
        "确认新进程已启动")
    
    # 9. 检查 downloads 目录中的文件
    run_command(ssh,
        'powershell -Command "Write-Host \\"Downloads 目录中的文件:\\"; Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" | Select-Object Name, @{Name=\\"Size(MB)\\";Expression={[math]::Round($_.Length/1MB,2)}}, LastWriteTime"',
        "检查待处理文件")
    
    # 10. 等待一段时间看是否开始处理
    print(f"\n⏳ 等待20秒，观察是否开始处理文件...")
    time.sleep(20)
    
    # 11. 检查是否有处理活动
    run_command(ssh,
        'powershell -Command "Write-Host \\"Processing 目录:\\"; Get-ChildItem \\"D:\\VideoTranscode\\processing\\" | Select-Object Name; Write-Host \\"\\n最新日志 (最后3行):\\"; if (Test-Path \\"D:\\VideoTranscode\\logs\\watcher.log\\") { Get-Content \\"D:\\VideoTranscode\\logs\\watcher.log\\" -Tail 3 }"',
        "检查处理活动")
    
    print("\n" + "=" * 50)
    print("✅ Watcher 服务重启完成!")
    print("📁 如果有文件在 downloads 目录，应该很快开始处理")
    
except Exception as e:
    print(f"❌ 重启失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()