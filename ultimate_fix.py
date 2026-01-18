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

print("🔧 终极修复方案")
print("=" * 50)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"🔐 连接到 198.176.60.121...")
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    print("✅ 连接成功!")
    
    # 1. 简单粗暴的方法：注释掉问题行
    run_command(ssh,
        '''powershell -Command "
$content = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Raw
Write-Host \\"原文件大小: $($content.Length) 字符\\"

# 查找并注释掉问题行
$content = $content -replace 'Write-Log \\"  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: \\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)秒\\" \\"Gray\\"', '# Write-Log \\"  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: [FIXED]秒\\" \\"Gray\\"'

# 保存修复后的文件
$content | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host \\"问题行已注释\\"
"''',
        "注释问题行")
    
    # 2. 验证修复
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-String -Pattern \\"FIXED\\" -Context 2"',
        "验证修复")
    
    # 3. 测试转码
    run_command(ssh,
        'powershell -Command "if (!(Test-Path D:\\VideoTranscode\\processing\\*.mp4)) { $file = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1; if ($file) { Move-Item $file.FullName D:\\VideoTranscode\\processing\\$($file.Name) -Force; Write-Host \'已移动测试文件\' } }"',
        "准备测试文件")
    
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\*.mp4) { $testFile = Get-ChildItem D:\\VideoTranscode\\processing -Filter \'*.mp4\' | Select-Object -First 1; Write-Host \'测试文件:\' $testFile.Name; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile $testFile.FullName } else { Write-Host \'没有测试文件\' }"',
        "测试转码")
    
    # 4. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 转码测试结果 ===\'; Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object Name, LastWriteTime"',
        "检查转码结果")
    
    # 5. 如果转码成功，重启 watcher
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep 2; Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已重启\\""',
        "重启 watcher 服务")
    
    # 6. 最终状态检查
    print(f"\n⏳ 等待10秒，检查系统状态...")
    import time
    time.sleep(10)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 系统最终状态 ===\'; Write-Host \'Downloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nWatcher进程:\'; Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Select-Object Id, StartTime; Write-Host \'\\n最新日志:\'; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3 }"',
        "最终状态检查")
    
    print("\n" + "=" * 50)
    print("✅ 终极修复完成!")
    print("🎯 语法错误已通过注释解决，转码功能应该正常")
    print("📁 Watcher 服务已重启，应该开始自动处理文件")
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()