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

print("🔍 调试 Watcher 问题")
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
    
    # 1. 检查 watcher 进程详细信息
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, ProcessName, StartTime, CommandLine"',
        "检查 watcher 进程详细信息")
    
    # 2. 手动测试 watcher 脚本语法
    run_command(ssh,
        'powershell -Command "powershell -NoProfile -NoLogo -Command \\"& { try { . D:\\VideoTranscode\\scripts\\watcher.ps1; Write-Host \'脚本加载成功\' } catch { Write-Host \'脚本错误:\' $_.Exception.Message } }\\" 2>&1"',
        "测试 watcher 脚本语法")
    
    # 3. 检查目录权限
    run_command(ssh,
        'powershell -Command "Write-Host \\"Downloads目录权限:\\"; Get-Acl \\"D:\\VideoTranscode\\downloads\\" | Select-Object Owner, AccessToString"',
        "检查目录权限")
    
    # 4. 检查文件详细信息
    run_command(ssh,
        'powershell -Command "Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" | ForEach-Object { Write-Host \\"文件: $($_.Name), 大小: $($_.Length), 扩展名: $($_.Extension), 可读: $(Test-Path $_.FullName -PathType Leaf)\\" }"',
        "检查文件详细信息")
    
    # 5. 手动运行一次文件检测逻辑
    run_command(ssh,
        'powershell -Command "$files = Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" -Filter \\"*.mp4\\"; Write-Host \\"找到 $($files.Count) 个 MP4 文件:\\"; $files | ForEach-Object { Write-Host \\"  - $($_.Name)\\" }"',
        "手动检测 MP4 文件")
    
    # 6. 检查日志文件权限
    run_command(ssh,
        'powershell -Command "if (Test-Path \\"D:\\VideoTranscode\\logs\\watcher.log\\") { Write-Host \\"日志文件存在，大小: $((Get-Item \\"D:\\VideoTranscode\\logs\\watcher.log\\").Length) 字节\\" } else { Write-Host \\"日志文件不存在\\" }"',
        "检查日志文件")
    
    # 7. 尝试手动处理一个文件
    run_command(ssh,
        'powershell -Command "if (Test-Path \\"D:\\VideoTranscode\\downloads\\1768543353686.mp4\\") { Write-Host \\"尝试手动移动文件...\\"; Move-Item \\"D:\\VideoTranscode\\downloads\\1768543353686.mp4\\" \\"D:\\VideoTranscode\\processing\\1768543353686.mp4\\" -Force; Write-Host \\"文件移动成功\\" } else { Write-Host \\"文件不存在\\" }"',
        "手动移动文件测试")
    
    # 8. 检查移动后的状态
    run_command(ssh,
        'powershell -Command "Write-Host \\"Downloads:\\"; Get-ChildItem \\"D:\\VideoTranscode\\downloads\\" | Select-Object Name; Write-Host \\"\\nProcessing:\\"; Get-ChildItem \\"D:\\VideoTranscode\\processing\\" | Select-Object Name"',
        "检查移动后状态")
    
    # 9. 如果文件移动成功，移回去
    run_command(ssh,
        'powershell -Command "if (Test-Path \\"D:\\VideoTranscode\\processing\\1768543353686.mp4\\") { Move-Item \\"D:\\VideoTranscode\\processing\\1768543353686.mp4\\" \\"D:\\VideoTranscode\\downloads\\1768543353686.mp4\\" -Force; Write-Host \\"文件已移回 downloads\\" }"',
        "移回文件")
    
    print("\n" + "=" * 50)
    print("✅ 调试完成!")
    print("💡 检查上面的输出，看看 watcher 为什么没有处理文件")
    
except Exception as e:
    print(f"❌ 调试失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()