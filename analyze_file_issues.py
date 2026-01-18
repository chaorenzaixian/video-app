#!/usr/bin/env python3
import paramiko
import sys

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

print("🔍 分析文件问题")
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
    
    # 1. 检查 long 和 short 是否是目录而不是文件
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 检查 long 和 short 的类型 ===\'; $long = Get-Item D:\\VideoTranscode\\downloads\\long; $short = Get-Item D:\\VideoTranscode\\downloads\\short; Write-Host \'long 类型:\' $long.GetType().Name; Write-Host \'short 类型:\' $short.GetType().Name; Write-Host \'long 是目录:\' $long.PSIsContainer; Write-Host \'short 是目录:\' $short.PSIsContainer"',
        "检查 long 和 short 的类型")
    
    # 2. 查看 long 和 short 目录内容
    run_command(ssh,
        'powershell -Command "Write-Host \'=== long 目录内容 ===\'; if (Test-Path D:\\VideoTranscode\\downloads\\long -PathType Container) { Get-ChildItem D:\\VideoTranscode\\downloads\\long | Select-Object Name, Length, Extension } else { Write-Host \'long 不是目录\' }; Write-Host \'\\n=== short 目录内容 ===\'; if (Test-Path D:\\VideoTranscode\\downloads\\short -PathType Container) { Get-ChildItem D:\\VideoTranscode\\downloads\\short | Select-Object Name, Length, Extension } else { Write-Host \'short 不是目录\' }"',
        "查看 long 和 short 目录内容")
    
    # 3. 检查 watcher 脚本是否处理子目录
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 脚本子目录处理逻辑 ===\"; Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-String -Pattern \'Recurse\|子目录\|subdirectory\' -Context 2"',
        "检查子目录处理逻辑")
    
    # 4. 手动检查所有 MP4 文件（包括子目录）
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 递归查找所有 MP4 文件 ===\'; Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' -Recurse | Select-Object FullName, Length, Directory"',
        "递归查找所有 MP4 文件")
    
    # 5. 检查我们创建的测试文件为什么没被处理
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 测试文件状态 ===\'; if (Test-Path D:\\VideoTranscode\\downloads\\test_filename_check.mp4) { $file = Get-Item D:\\VideoTranscode\\downloads\\test_filename_check.mp4; Write-Host \'文件存在，大小:\' $file.Length \'字节\'; Write-Host \'扩展名:\' $file.Extension; Write-Host \'是否符合过滤条件:\'; $符合 = ($file.Extension -eq \'.mp4\') -and ($file.Length -gt 1000); Write-Host $符合 } else { Write-Host \'测试文件不存在\' }"',
        "检查测试文件状态")
    
    # 6. 手动触发 watcher 检测逻辑
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 手动执行文件检测逻辑 ===\'; $videoFiles = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' -File | Where-Object { $_.Length -gt 1000 }; Write-Host \'找到的视频文件数量:\' $videoFiles.Count; $videoFiles | ForEach-Object { Write-Host \'文件:\' $_.Name \'大小:\' $_.Length }"',
        "手动执行文件检测逻辑")
    
    # 7. 检查 watcher 进程是否真的在工作
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 进程详情 ===\'; Get-Process powershell | Where-Object { $_.CommandLine -like \'*watcher*\' } | Select-Object Id, ProcessName, StartTime, @{Name=\'WorkingSet(MB)\';Expression={[math]::Round($_.WorkingSet/1MB,2)}}, @{Name=\'CPU\';Expression={$_.CPU}}"',
        "检查 watcher 进程详情")
    
    # 8. 查看 watcher 脚本的循环逻辑
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 循环逻辑 ===\'; Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-String -Pattern \'while\|Start-Sleep\|循环\' -Context 1"',
        "查看 watcher 循环逻辑")
    
    print("\n" + "=" * 50)
    print("🔍 分析完成!")
    print("\n💡 可能的问题:")
    print("1. long 和 short 是目录，不是文件")
    print("2. watcher 可能不处理子目录中的文件")
    print("3. 测试文件可能没有被正确检测")
    print("4. watcher 进程可能没有正常工作")
    
except Exception as e:
    print(f"❌ 分析失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()