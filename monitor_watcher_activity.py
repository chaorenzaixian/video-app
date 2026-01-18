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

print("👀 监控 Watcher 活动")
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
    
    # 监控3次，每次间隔15秒
    for i in range(3):
        print(f"\n{'='*50}")
        print(f"📊 第 {i+1} 次检查 ({time.strftime('%H:%M:%S')})")
        print(f"{'='*50}")
        
        # 1. 检查进程
        run_command(ssh,
            'powershell -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.WS -gt 10MB } | Select-Object Id, @{Name=\'Memory(MB)\';Expression={[math]::Round($_.WS/1MB,2)}}, StartTime"',
            "Watcher 进程状态")
        
        # 2. 检查目录
        run_command(ssh,
            'powershell -Command "Write-Host \'Downloads:\'; $d = Get-ChildItem D:\\VideoTranscode\\downloads -Filter *.mp4 -File -ErrorAction SilentlyContinue; if ($d) { $d | Select-Object Name } else { Write-Host \'  (空)\' }; Write-Host \'Processing:\'; $p = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Name } else { Write-Host \'  (空)\' }; Write-Host \'Completed (最新5个):\'; Get-ChildItem D:\\VideoTranscode\\completed -Filter *.mp4 -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime"',
            "目录状态")
        
        # 3. 检查最新日志
        run_command(ssh,
            'powershell -Command "if (Test-Path D:\\VideoTranscode\\logs\\watcher.log) { Write-Host \'最新3条日志:\'; Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 3 } else { Write-Host \'无日志\' }"',
            "最新日志")
        
        if i < 2:
            print(f"\n⏳ 等待15秒后继续监控...")
            time.sleep(15)
    
    print("\n" + "=" * 50)
    print("📊 监控完成!")
    print("\n💡 分析:")
    print("- 如果 downloads 中的文件消失了，说明 watcher 正在工作")
    print("- 如果文件出现在 processing，说明正在转码")
    print("- 如果文件出现在 completed，说明转码完成")
    print("- 如果文件一直在 downloads，说明 watcher 没有处理")
    
except Exception as e:
    print(f"❌ 监控失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
