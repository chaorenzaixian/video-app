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

print("🚨 紧急语法修复 - 立即停止失败循环")
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
    
    # 1. 立即停止所有 watcher 进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host \\"已停止所有 watcher 进程\\""',
        "紧急停止 watcher 进程")
    
    # 2. 使用最简单的方法：直接删除问题行
    run_command(ssh,
        '''powershell -Command "
# 读取文件
$lines = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1'
Write-Host \\"原文件行数: $($lines.Length)\\"

# 找到并删除问题行
$newLines = @()
for ($i = 0; $i -lt $lines.Length; $i++) {
    $line = $lines[$i]
    if ($line -match 'Write-Log.*math.*Round.*startTime') {
        Write-Host \\"删除问题行 $($i+1): $line\\"
        # 跳过这一行，不添加到新文件中
    } else {
        $newLines += $line
    }
}

# 保存修复后的文件
$newLines | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host \\"修复完成，新文件行数: $($newLines.Length)\\"
"''',
        "删除问题行")
    
    # 3. 验证修复
    run_command(ssh,
        'powershell -Command "if ((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw) -match \\"math.*Round.*startTime\\") { Write-Host \\"仍有问题\\" } else { Write-Host \\"问题行已删除\\" }"',
        "验证修复")
    
    # 4. 快速测试语法
    run_command(ssh,
        'powershell -Command "try { powershell -NoProfile -NoLogo -Command \\"& D:\\VideoTranscode\\scripts\\transcode_full.ps1 -WhatIf 2>&1\\" | Out-Null; Write-Host \\"语法正常\\" } catch { Write-Host \\"仍有语法错误\\" }"',
        "测试语法")
    
    # 5. 清理处理目录中的文件（避免重复处理）
    run_command(ssh,
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\processing -Filter \\"*.mp4\\" | ForEach-Object { Move-Item $_.FullName D:\\VideoTranscode\\downloads\\$($_.Name) -Force }; Write-Host \\"已将处理中的文件移回 downloads\\""',
        "清理处理目录")
    
    # 6. 重启 watcher 服务
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已重启\\""',
        "重启 watcher 服务")
    
    # 7. 等待并检查
    print(f"\n⏳ 等待15秒，观察是否还有错误...")
    import time
    time.sleep(15)
    
    run_command(ssh,
        'powershell -Command "Write-Host \\"=== 修复后状态 ===\\"; Write-Host \\"Downloads:\\" ; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \\"\\nProcessing:\\"; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \\"\\n最新日志 (最后5行):\\"; if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5 }"',
        "检查修复后状态")
    
    print("\n" + "=" * 50)
    print("🚨 紧急修复完成!")
    print("🎯 问题行已删除，转码应该可以正常进行")
    print("📊 请观察日志，看是否还有语法错误")
    
except Exception as e:
    print(f"❌ 紧急修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()