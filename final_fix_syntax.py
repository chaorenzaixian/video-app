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

print("🔧 最终修复语法错误")
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
    
    # 1. 备份当前脚本
    run_command(ssh,
        'powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\transcode_full.ps1 D:\\VideoTranscode\\scripts\\transcode_full_backup_final.ps1 -Force"',
        "备份当前脚本")
    
    # 2. 查看第219行的具体内容
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-Object -Skip 218 -First 3 | ForEach-Object { Write-Host \\"Line $((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-Object -First 221).Count - 2): $_\\" }"',
        "查看第219行内容")
    
    # 3. 使用更精确的替换来修复语法错误
    fix_cmd = '''powershell -Command "
$content = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Raw

# 查找并替换所有包含 [math]::Round 的问题行
$lines = $content -split '\\r?\\n'
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match '\\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)') {
        Write-Host \\"找到问题行 $($i+1): $($lines[$i])\\"
        # 替换为正确的语法
        $lines[$i] = $lines[$i] -replace '\\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)', '\\$([math]::Round(\\$startTime, 1))'
        Write-Host \\"修复后: $($lines[$i])\\"
    }
}

# 重新组合内容并保存
$newContent = $lines -join \\\"\\r\\n\\\"
$newContent | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host \\"修复完成\\"
"'''
    
    run_command(ssh, fix_cmd, "精确修复语法错误")
    
    # 4. 验证修复
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-Object -Skip 218 -First 3"',
        "验证修复结果")
    
    # 5. 测试脚本语法
    run_command(ssh,
        'powershell -Command "powershell -NoProfile -NoLogo -Command \\"try { . D:\\VideoTranscode\\scripts\\transcode_full.ps1; Write-Host \'脚本语法正确\' } catch { Write-Host \'语法错误:\' \\$_.Exception.Message }\\" 2>&1"',
        "测试脚本语法")
    
    # 6. 如果还有问题，使用更简单的方法
    run_command(ssh,
        'powershell -Command "if ((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw) -match \\"\\[math\\]::Round\\(\\\\\\$startTime\\") { Write-Host \\"仍有语法问题，使用简单替换\\"; (Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw) -replace \\"\\\\\\$\\\\\\(\\\\\\[math\\\\\\]::Round\\\\\\(\\\\\\\\\\$startTime, 1\\\\\\)\\\\\\)\\", \\"\\\\\\${roundedTime}\\" | Set-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Encoding UTF8 }"',
        "备用修复方案")
    
    # 7. 手动测试转码
    print(f"\n🧪 测试修复后的转码...")
    run_command(ssh,
        'powershell -Command "if (Test-Path D:\\VideoTranscode\\processing\\1768543353686.mp4) { cd D:\\VideoTranscode\\scripts; powershell -ExecutionPolicy Bypass -File .\\transcode_full.ps1 -InputFile D:\\VideoTranscode\\processing\\1768543353686.mp4 } else { Write-Host \'测试文件不存在\' }"',
        "测试转码功能")
    
    # 8. 检查结果
    run_command(ssh,
        'powershell -Command "Write-Host \'Processing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\nCompleted (最新5个):\'; Get-ChildItem D:\\VideoTranscode\\completed | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Select-Object Name, LastWriteTime"',
        "检查转码结果")
    
    print("\n" + "=" * 50)
    print("✅ 最终语法修复完成!")
    print("🎯 如果转码成功，语法问题已解决")
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()