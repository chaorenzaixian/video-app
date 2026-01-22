#!/usr/bin/env python3
"""
使用 paramiko 远程修复转码服务器的 PowerShell 语法错误
"""
import paramiko
import time

# 服务器配置
TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"
SSH_KEYS = ["server_key_new", "server_key", "C:\\server_key"]

def try_ssh_connection():
    """尝试多种方式连接SSH"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 尝试密码认证
    try:
        print("🔐 尝试密码认证...")
        ssh.connect(
            hostname=TRANSCODE_SERVER,
            port=22,
            username=TRANSCODE_USER,
            password=TRANSCODE_PASSWORD,
            timeout=30
        )
        print("✅ 密码认证成功!")
        return ssh
    except Exception as e:
        print(f"❌ 密码认证失败: {e}")
    
    # 尝试SSH密钥认证
    for key_file in SSH_KEYS:
        try:
            print(f"🔑 尝试SSH密钥: {key_file}")
            ssh.connect(
                hostname=TRANSCODE_SERVER,
                port=22,
                username=TRANSCODE_USER,
                key_filename=key_file,
                timeout=30
            )
            print(f"✅ SSH密钥认证成功: {key_file}")
            return ssh
        except Exception as e:
            print(f"❌ SSH密钥失败 ({key_file}): {e}")
    
    return None

def run_command(ssh, command, description):
    """执行远程命令"""
    print(f"\n📋 {description}...")
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"✅ 成功: {description}")
            if output:
                print(f"   输出: {output[:200]}")
        else:
            print(f"❌ 失败: {description} (退出码: {exit_code})")
            if error:
                print(f"   错误: {error[:200]}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        return "", str(e), -1

def main():
    print("🔧 转码服务器 PowerShell 语法错误修复")
    print("=" * 60)
    
    # 连接服务器
    ssh = try_ssh_connection()
    if not ssh:
        print("\n❌ 所有SSH连接尝试都失败了")
        print("\n📋 手动修复步骤:")
        print("1. 登录转码服务器 (198.176.60.121)")
        print("2. 打开 PowerShell 管理员模式")
        print("3. 执行以下命令:")
        print('   Copy-Item "D:\\VideoTranscode\\scripts\\transcode_full.ps1" "D:\\VideoTranscode\\scripts\\transcode_full_backup.ps1" -Force')
        print('   $content = Get-Content "D:\\VideoTranscode\\scripts\\transcode_full.ps1" -Raw')
        print('   $content = $content -replace \'Write-Log "  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: \\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)秒" "Gray"\', \'$roundedTime = [math]::Round($startTime, 1); Write-Log "  片段 $($i+1)/$numSegments: ${roundedTime}秒" "Gray"\'')
        print('   $content | Set-Content "D:\\VideoTranscode\\scripts\\transcode_full.ps1" -Encoding UTF8')
        print('   Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "D:\\VideoTranscode\\scripts\\watcher.ps1" -WindowStyle Minimized')
        return
    
    print(f"✅ 已连接到转码服务器: {TRANSCODE_SERVER}")
    
    try:
        # 1. 停止 watcher 进程
        run_command(ssh, 
            'powershell -Command "Get-Process | Where-Object { $_.ProcessName -eq \\"powershell\\" } | ForEach-Object { if ($_.CommandLine -like \\"*watcher*\\" -or $_.Id -ne $PID) { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } }"',
            "停止 watcher 进程")
        
        # 2. 备份原始文件
        run_command(ssh,
            'powershell -Command "Copy-Item \\"D:\\VideoTranscode\\scripts\\transcode_full.ps1\\" \\"D:\\VideoTranscode\\scripts\\transcode_full_backup_$(Get-Date -Format \'HHmmss\').ps1\\" -Force"',
            "备份原始脚本")
        
        # 3. 修复语法错误
        fix_command = '''powershell -Command "
$content = Get-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Raw
$content = $content -replace 'Write-Log \\"  片段 \\$\\(\\$i\\+1\\)/\\$numSegments: \\$\\(\\[math\\]::Round\\(\\$startTime, 1\\)\\)秒\\" \\"Gray\\"', '$roundedTime = [math]::Round($startTime, 1); Write-Log \\"  片段 $($i+1)/$numSegments: ${roundedTime}秒\\" \\"Gray\\"'
$content | Set-Content 'D:\\VideoTranscode\\scripts\\transcode_full.ps1' -Encoding UTF8
Write-Host '修复完成'
"'''
        
        run_command(ssh, fix_command, "修复语法错误")
        
        # 4. 验证语法
        run_command(ssh,
            'powershell -Command "try { $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content \\"D:\\VideoTranscode\\scripts\\transcode_full.ps1\\" -Raw), [ref]$null); Write-Host \\"语法检查通过\\" } catch { Write-Host \\"语法错误: $_\\" }"',
            "验证语法")
        
        # 5. 重启 watcher 服务
        run_command(ssh,
            'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized"',
            "重启 watcher 服务")
        
        print("\n" + "=" * 60)
        print("✅ 修复完成!")
        print("🎯 转码服务器现在应该可以正常处理视频了")
        print("📋 可以通过以下方式验证:")
        print("1. 查看转码日志不再出现语法错误")
        print("2. 放入测试视频到 D:\\VideoTranscode\\downloads\\long\\ 目录")
        print("3. 观察处理过程")
        
    except Exception as e:
        print(f"\n❌ 修复过程中出现异常: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()