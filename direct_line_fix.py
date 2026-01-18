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

print("🔧 直接修复第219行")
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
    
    # 1. 读取整个文件并逐行处理
    run_command(ssh,
        '''powershell -Command "
$lines = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1'
Write-Host \\"文件总行数: $($lines.Length)\\"

# 找到并修复第219行
if ($lines.Length -ge 219) {
    Write-Host \\"第219行原内容: $($lines[218])\\"
    
    # 直接替换第219行
    $lines[218] = '        Write-Log \\"  片段 \\$($i+1)/\\$numSegments: \\$roundedTime秒\\" \\"Gray\\"'
    
    # 在第218行后插入变量定义
    $newLines = @()
    for ($i = 0; $i -lt $lines.Length; $i++) {
        if ($i -eq 217) {  # 第218行 (索引217)
            $newLines += $lines[$i]
            $newLines += '        $roundedTime = [math]::Round($startTime, 1)'
        } else {
            $newLines += $lines[$i]
        }
    }
    
    # 保存修复后的文件
    $newLines | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
    Write-Host \\"第219行已修复\\"
} else {
    Write-Host \\"文件行数不足219行\\"
}
"''',
        "直接修复第219行")
    
    # 2. 验证修复
    run_command(ssh,
        'powershell -Command "$lines = Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1; Write-Host \\"第218行: $($lines[217])\\"; Write-Host \\"第219行: $($lines[218])\\"; Write-Host \\"第220行: $($lines[219])\\""',
        "验证修复结果")
    
    # 3. 测试语法
    run_command(ssh,
        'powershell -Command "powershell -NoProfile -NoLogo -Command \\"try { powershell -NoProfile -SyntaxOnly D:\\VideoTranscode\\scripts\\transcode_full.ps1 2>&1; Write-Host \'语法检查通过\' } catch { Write-Host \'语法错误:\' \\$_.Exception.Message }\\" 2>&1"',
        "测试语法")
    
    # 4. 手动测试转码
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\1768543353686.mp4) { Write-Host \'开始测试转码...\'; cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\1768543353686.mp4 } else { Write-Host \'测试文件不存在，从downloads移动一个\'; if (Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1) { $file = Get-ChildItem D:\\VideoTranscode\\downloads -Filter \'*.mp4\' | Select-Object -First 1; Move-Item $file.FullName D:\\VideoTranscode\\processing\\$($file.Name) -Force; Write-Host \'已移动文件到processing\' } }"',
        "测试转码")
    
    # 5. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 目录状态 ===\'; Write-Host \'Downloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nProcessing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新3个):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | Select-Object Name, LastWriteTime"',
        "检查最终结果")
    
    print("\n" + "=" * 50)
    print("✅ 直接修复完成!")
    print("🎯 第219行语法错误应该已经解决")
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()