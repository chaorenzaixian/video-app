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
                lines = output.split('\n')[:15]
                print(f"   输出: {chr(10).join(lines)}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error[:500]}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("🔧 创建并启动干净的 Watcher 服务")
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
    
    # 1. 停止所有现有进程
    run_command(ssh,
        'taskkill /F /FI "WINDOWTITLE eq watcher*" 2>nul & taskkill /F /FI "IMAGENAME eq powershell.exe" /FI "MEMUSAGE gt 10000" 2>nul & echo 已清理进程',
        "清理现有进程")
    
    time.sleep(3)
    
    # 2. 使用 watcher_full.ps1（我们知道这个是好的）
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\scripts\\watcher_full.ps1) { Copy-Item D:\\VideoTranscode\\scripts\\watcher_full.ps1 D:\\VideoTranscode\\scripts\\watcher.ps1 -Force; Write-Host \'已复制 watcher_full.ps1\' } else { Write-Host \'watcher_full.ps1 不存在\' }"',
        "复制正确的 watcher 脚本")
    
    # 3. 验证脚本
    run_command(ssh,
        'powershell -Command "Write-Host \'脚本大小:\'; (Get-Item D:\\VideoTranscode\\scripts\\watcher.ps1).Length; Write-Host \'前15行:\'; Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-Object -First 15"',
        "验证脚本")
    
    # 4. 使用 Start-Process 启动
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy Bypass -NoExit -Command & D:\\VideoTranscode\\scripts\\watcher.ps1\' -WindowStyle Normal; Write-Host \'已启动 watcher\'"',
        "启动 watcher 服务")
    
    time.sleep(5)
    
    # 5. 检查进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Select-Object Id, StartTime, @{Name=\'Memory(MB)\';Expression={[math]::Round($_.WS/1MB,2)}} | Format-Table"',
        "检查 PowerShell 进程")
    
    # 6. 检查日志
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Write-Host \'最新日志:\'; Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 } else { Write-Host \'日志文件不存在\' }"',
        "检查日志")
    
    # 7. 检查待处理文件
    run_command(ssh,
        'powershell -Command "Write-Host \'Downloads 目录:\'; Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File | Select-Object Name, @{Name=\'Size(KB)\';Expression={[math]::Round($_.Length/1KB,2)}}"',
        "检查待处理文件")
    
    print("\n" + "=" * 50)
    print("✅ Watcher 服务已重新创建并启动!")
    print("\n📝 后续步骤:")
    print("1. 观察日志文件: D:\\VideoTranscode\\logs\\watcher.log")
    print("2. 如果有文件在 downloads 目录，应该会被自动处理")
    print("3. 可以手动放入测试文件验证")
    
except Exception as e:
    print(f"❌ 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
