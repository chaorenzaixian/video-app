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

print("🚨 最终紧急修复 - 直接替换问题行")
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
    
    # 1. 停止所有进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Stop-Process -Force -ErrorAction SilentlyContinue"',
        "停止所有进程")
    
    # 2. 使用 sed 风格的替换来修复问题
    run_command(ssh,
        '''powershell -Command "
# 读取文件内容
$content = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Raw

# 显示原始问题
Write-Host \\"查找问题行...\\"
if ($content -match 'Write-Log.*math.*Round.*startTime') {
    Write-Host \\"找到问题行\\"
} else {
    Write-Host \\"未找到问题行\\"
}

# 使用简单的字符串替换
$content = $content -replace 'Write-Log \\"  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: \\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)秒\\" \\"Gray\\"', 'Write-Log \\"  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: [时间]秒\\" \\"Gray\\"'

# 保存文件
$content | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host \\"替换完成\\"
"''',
        "替换问题行")
    
    # 3. 验证替换结果
    run_command(ssh,
        'powershell -Command "if ((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw) -match \\"\\[时间\\]\\") { Write-Host \\"替换成功\\" } else { Write-Host \\"替换失败\\" }"',
        "验证替换结果")
    
    # 4. 再次检查是否还有问题行
    run_command(ssh,
        'powershell -Command "if ((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw) -match \\"math.*Round.*startTime\\") { Write-Host \\"仍有问题行\\" } else { Write-Host \\"问题行已清除\\" }"',
        "检查是否还有问题")
    
    # 5. 测试转码
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\test_manual.mp4) { Write-Host \'测试转码...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\test_manual.mp4 } else { Write-Host \'测试文件不存在\' }"',
        "测试转码")
    
    # 6. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object Name, LastWriteTime"',
        "检查转码结果")
    
    # 7. 如果成功，重启 watcher
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized; Write-Host \\"Watcher 已重启\\""',
        "重启 watcher")
    
    print("\n" + "=" * 50)
    print("🚨 最终修复完成!")
    print("🎯 问题行已替换为简单文本")
    print("📊 请检查转码是否成功")
    
except Exception as e:
    print(f"❌ 最终修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()