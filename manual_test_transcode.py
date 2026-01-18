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
        stdin, stdout, stderr = ssh.exec_command(command, timeout=120)
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

print("🧪 手动测试转码功能")
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
    
    # 1. 检查当前文件
    run_command(ssh,
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\downloads | Where-Object { $_.Extension -eq \'.mp4\' -and $_.Length -gt 1000 } | Select-Object Name, @{Name=\'Size(MB)\';Expression={[math]::Round($_.Length/1MB,2)}}"',
        "检查可处理的视频文件")
    
    # 2. 手动移动一个文件到处理目录
    run_command(ssh,
        'powershell -Command "if (Test-Path \'D:\\VideoTranscode\\downloads\\1768543353686.mp4\') { Move-Item \'D:\\VideoTranscode\\downloads\\1768543353686.mp4\' \'D:\\VideoTranscode\\processing\\1768543353686.mp4\' -Force; Write-Host \'文件已移动到处理目录\' } else { Write-Host \'文件不存在\' }"',
        "移动文件到处理目录")
    
    # 3. 检查移动结果
    run_command(ssh,
        'powershell -Command "Write-Host \'Processing目录:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name, @{Name=\'Size(MB)\';Expression={[math]::Round($_.Length/1MB,2)}}"',
        "检查处理目录")
    
    # 4. 手动调用转码脚本
    print(f"\n🎬 开始手动转码测试...")
    run_command(ssh,
        'powershell -Command "cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\1768543353686.mp4"',
        "手动执行转码")
    
    # 5. 检查转码结果
    run_command(ssh,
        'powershell -Command "Write-Host \'Processing目录:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted目录:\'; Get-ChildItem D:\\VideoTranscode\\completed | Select-Object Name, @{Name=\'Size(MB)\';Expression={[math]::Round($_.Length/1MB,2)}} | Sort-Object Name -Descending | Select-Object -First 5"',
        "检查转码结果")
    
    # 6. 检查最新的转码日志
    run_command(ssh,
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs -Filter \'transcode_*.log\' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { Write-Host \'最新转码日志:\'; Get-Content $_.FullName -Tail 10 }"',
        "检查转码日志")
    
    print("\n" + "=" * 50)
    print("✅ 手动转码测试完成!")
    print("💡 如果转码成功，说明脚本修复有效，只需要修复 watcher 监控")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()