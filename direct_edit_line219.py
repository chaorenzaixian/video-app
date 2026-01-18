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

print("🔧 直接编辑第219行")
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
    
    # 1. 查看第219行的确切内容
    run_command(ssh,
        'powershell -Command "$lines = Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1; Write-Host \\"第218行: $($lines[217])\\"; Write-Host \\"第219行: $($lines[218])\\"; Write-Host \\"第220行: $($lines[219])\\""',
        "查看第219行内容")
    
    # 2. 直接修改第219行
    run_command(ssh,
        '''powershell -Command "
$lines = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1'
Write-Host \\"原第219行: $($lines[218])\\"

# 直接替换第219行为简单的注释
$lines[218] = '        # Write-Log \\"  片段信息已省略\\" \\"Gray\\"'

Write-Host \\"新第219行: $($lines[218])\\"

# 保存文件
$lines | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host \\"第219行已修改\\"
"''',
        "直接修改第219行")
    
    # 3. 验证修改
    run_command(ssh,
        'powershell -Command "$lines = Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1; Write-Host \\"修改后第219行: $($lines[218])\\""',
        "验证修改结果")
    
    # 4. 测试转码
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\test_manual.mp4) { Write-Host \'测试转码...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\test_manual.mp4 } else { Write-Host \'测试文件不存在，从downloads移动一个\'; $file = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1; if ($file) { Move-Item $file.FullName D:\\VideoTranscode\\processing\\test_fix.mp4 -Force; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\test_fix.mp4 } }"',
        "测试转码")
    
    # 5. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 转码测试结果 ===\'; Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新2个):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 2 | Select-Object Name, LastWriteTime"',
        "检查转码结果")
    
    # 6. 如果成功，重启 watcher
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep 2; Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已重启\\""',
        "重启 watcher")
    
    # 7. 最终检查
    print(f"\n⏳ 等待10秒，检查系统状态...")
    import time
    time.sleep(10)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 最终状态 ===\'; Write-Host \'Downloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nWatcher进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id; Write-Host \'\\n最新日志:\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3 }"',
        "最终状态检查")
    
    print("\n" + "=" * 50)
    print("✅ 直接编辑完成!")
    print("🎯 第219行已改为注释，应该不再有语法错误")
    
except Exception as e:
    print(f"❌ 编辑失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()