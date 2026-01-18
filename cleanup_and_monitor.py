#!/usr/bin/env python3
import paramiko
import sys
import time

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
                print(f"   错误: {error[:300]}")
        
        return output, error, exit_code
    except Exception as e:
        print(f"❌ 异常: {e}")
        return "", str(e), -1

print("🧹 清理无效文件并监控系统")
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
    
    # 1. 清理 processing 目录中的无效文件
    run_command(ssh,
        'powershell -Command "Write-Host \'清理 processing 目录...\'; Get-ChildItem D:\\VideoTranscode\\processing -Filter test_*.mp4 -File -ErrorAction SilentlyContinue | Remove-Item -Force; Write-Host \'已清理\'"',
        "清理无效文件")
    
    # 2. 检查 downloads 目录
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Downloads 目录 ===\'; Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File -ErrorAction SilentlyContinue | Select-Object Name, @{Name=\'Size(KB)\';Expression={[math]::Round($_.Length/1KB,2)}}"',
        "检查 downloads 目录")
    
    # 3. 检查 watcher 进程
    run_command(ssh,
        'powershell -Command "Write-Host \'=== Watcher 进程 ===\'; $procs = Get-WmiObject Win32_Process -Filter \\"name=\'powershell.exe\'\\" | Where-Object { $_.CommandLine -like \'*watcher*\' }; if ($procs) { Write-Host \'✅ Watcher 运行中 (PID:\' $procs.ProcessId \')\' } else { Write-Host \'❌ Watcher 未运行\' }"',
        "检查 watcher 进程")
    
    # 4. 监控30秒，看 watcher 是否处理新文件
    print("\n" + "=" * 50)
    print("⏳ 监控30秒，观察 watcher 是否处理文件...")
    print("=" * 50)
    
    for i in range(3):
        print(f"\n📊 检查 {i+1}/3 ({time.strftime('%H:%M:%S')})")
        
        # 检查目录状态
        output, _, _ = run_command(ssh,
            'powershell -Command "Write-Host \'Downloads:\'; $d = Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File -ErrorAction SilentlyContinue; if ($d) { $d.Count } else { Write-Host \'0\' }; Write-Host \'Processing:\'; $p = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File -ErrorAction SilentlyContinue; if ($p) { $p.Count } else { Write-Host \'0\' }"',
            "目录状态")
        
        # 查看最新日志
        run_command(ssh,
            'powershell -Command "if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3 } else { Write-Host \'无日志\' }"',
            "最新日志")
        
        if i < 2:
            print(f"\n⏳ 等待10秒...")
            time.sleep(10)
    
    # 5. 最终状态
    print("\n" + "=" * 50)
    print("📊 最终状态")
    print("=" * 50)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 各目录文件数 ===\'; Write-Host \'Downloads:\' (Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File -ErrorAction SilentlyContinue).Count; Write-Host \'Processing:\' (Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File -ErrorAction SilentlyContinue).Count; Write-Host \'Completed:\' (Get-ChildItem D:\\VideoTranscode\\completed -Filter *.mp4 -File -ErrorAction SilentlyContinue).Count"',
        "文件统计")
    
    run_command(ssh,
        'powershell -Command "Write-Host \'=== 最新转码日志 ===\'; if (Test-Path D:\\VideoTranscode\\logs\\transcode.log) { Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 10 } else { Write-Host \'无转码日志\' }"',
        "转码日志")
    
    print("\n" + "=" * 50)
    print("✅ 监控完成")
    print("\n💡 分析:")
    print("- 如果 downloads 中的文件被处理，说明 watcher 正常工作")
    print("- 如果转码日志有新内容，说明转码功能正常")
    print("- 如果 completed 目录有新文件，说明整个流程正常")
    
except Exception as e:
    print(f"❌ 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
