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
                print(f"{output}")
        else:
            print(f"❌ 失败 (退出码: {exit_code})")
            if error:
                print(f"   错误: {error[:500]}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("🔍 诊断转码失败原因")
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
    
    # 1. 查看完整的 watcher 日志
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 完整 Watcher 日志（最新20条）===\'; Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"',
        "查看完整日志")
    
    # 2. 检查转码日志
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 转码日志 ===\'; if (Test-Path D:\\VideoTranscode\\logs\\transcode.log) { Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 20 } else { Write-Host \'转码日志不存在\' }"',
        "查看转码日志")
    
    # 3. 检查 processing 目录中是否有残留文件
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Processing 目录 ===\'; Get-ChildItem D:\\VideoTranscode\\processing -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime"',
        "检查 processing 目录")
    
    # 4. 检查转码脚本是否存在
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 转码脚本检查 ===\'; if (Test-Path D:\\VideoTranscode\\scripts\\transcode_full.ps1) { Write-Host \'✅ transcode_full.ps1 存在\'; $script = Get-Item D:\\VideoTranscode\\scripts\\transcode_full.ps1; Write-Host \'大小:\' $script.Length \'字节\' } else { Write-Host \'❌ transcode_full.ps1 不存在\' }"',
        "检查转码脚本")
    
    # 5. 测试 FFmpeg 是否可用
    run_command(ssh,
        'powershell -Command "Write-Host \'=== FFmpeg 测试 ===\'; try { $version = & ffmpeg -version 2>&1 | Select-Object -First 1; Write-Host \'✅ FFmpeg 可用:\' $version } catch { Write-Host \'❌ FFmpeg 不可用\' }"',
        "测试 FFmpeg")
    
    # 6. 查看 watcher 脚本中的转码调用
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 脚本中的转码调用 ===\'; Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-String -Pattern \'transcode\' -Context 2,2"',
        "查看转码调用")
    
    # 7. 手动测试转码（如果 processing 中有文件）
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 手动测试转码 ===\'; $testFile = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File -ErrorAction SilentlyContinue | Select-Object -First 1; if ($testFile) { Write-Host \'测试文件:\' $testFile.Name; Write-Host \'执行转码...\'; & powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\transcode_full.ps1 -InputFile $testFile.FullName 2>&1 | Select-Object -First 10 } else { Write-Host \'Processing 目录中没有文件可测试\' }"',
        "手动测试转码")
    
    print("\n" + "=" * 50)
    print("📊 诊断完成")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
