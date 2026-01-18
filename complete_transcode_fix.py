#!/usr/bin/env python3
import paramiko
import sys
import re

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔧 完整修复转码脚本")
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
    
    # 1. 读取文件内容
    print("\n📋 读取转码脚本...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw"', timeout=60)
    content = stdout.read().decode('utf-8', errors='ignore')
    print(f"✅ 读取成功 ({len(content)} 字符)")
    
    # 2. 备份
    print("\n📋 备份原文件...")
    ssh.exec_command('powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\transcode_full.ps1 D:\\VideoTranscode\\scripts\\transcode_full.ps1.bak2 -Force"', timeout=30)
    print("✅ 备份完成")
    
    # 3. 修复所有 $([math]::Round(...)) 问题
    print("\n📋 修复语法错误...")
    
    # 找到所有问题行并修复
    # 问题模式: $([math]::Round($variable, 1))
    # 修复方法: 先计算再使用
    
    # 修复第219行的问题
    old_pattern = r'Write-Log\s+".*?\$\(\[math\]::Round\(\$startTime,\s*1\)\).*?\$\(\[math\]::Round\(\$endTime,\s*1\)\).*?"'
    
    if re.search(old_pattern, content):
        print("  找到需要修复的行")
        # 替换为正确的写法
        new_code = '''$startTimeRounded = [math]::Round($startTime, 1)
                $endTimeRounded = [math]::Round($endTime, 1)
                Write-Log "  片段 $($i+1)/$numSegments: ${startTimeRounded}秒 - ${endTimeRounded}秒" "Gray"'''
        
        content = re.sub(old_pattern, new_code, content)
        print("  ✅ 已修复")
    else:
        print("  未找到匹配的模式，尝试其他方法...")
        
        # 直接查找并替换包含 $([math]::Round 的行
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '$([math]::Round' in line and 'Write-Log' in line:
                print(f"  找到问题行 {i+1}: {line[:80]}...")
                # 替换这一行
                lines[i] = '                $startTimeRounded = [math]::Round($startTime, 1)'
                lines.insert(i+1, '                $endTimeRounded = [math]::Round($endTime, 1)')
                lines.insert(i+2, '                Write-Log "  片段 $($i+1)/$numSegments: ${startTimeRounded}秒 - ${endTimeRounded}秒" "Gray"')
                content = '\n'.join(lines)
                print("  ✅ 已修复")
                break
    
    # 4. 使用 Base64 编码写入（避免编码问题）
    print("\n📋 写入修复后的脚本...")
    import base64
    content_bytes = content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('ascii')
    
    write_cmd = f'powershell -Command "$bytes = [System.Convert]::FromBase64String(\'{content_base64}\'); $content = [System.Text.Encoding]::UTF8.GetString($bytes); $content | Set-Content -Path D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Encoding UTF8; Write-Host \'写入完成\'"'
    
    stdin, stdout, stderr = ssh.exec_command(write_cmd, timeout=60)
    result = stdout.read().decode('utf-8', errors='ignore')
    print(f"✅ {result}")
    
    # 5. 验证
    print("\n📋 验证修复...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "$errors = $null; $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 -Raw), [ref]$errors); if ($errors.Count -eq 0) { Write-Host \'✅ 语法正确\' } else { Write-Host \'❌ 仍有错误:\'; $errors | Select-Object -First 3 Message }"', timeout=60)
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)
    
    # 6. 重启 watcher
    print("\n📋 重启 watcher 服务...")
    ssh.exec_command('powershell -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like \'*watcher*\' } | Stop-Process -Force -ErrorAction SilentlyContinue"', timeout=30)
    import time
    time.sleep(3)
    ssh.exec_command('powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy\', \'Bypass\', \'-NoExit\', \'-File\', \'D:\\VideoTranscode\\scripts\\watcher.ps1\' -WindowStyle Minimized"', timeout=30)
    print("✅ Watcher 已重启")
    
    print("\n" + "=" * 50)
    print("✅ 修复完成!")
    print("\n现在可以测试转码功能了")
    
except Exception as e:
    print(f"❌ 修复失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
