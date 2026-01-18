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

print("🔧 创建简单可靠的 Watcher 脚本")
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
    
    # 1. 停止当前进程
    run_command(ssh,
        'powershell -Command "Get-Process powershell | Where-Object { $_.CommandLine -like \\"*watcher*\\" } | Stop-Process -Force -ErrorAction SilentlyContinue"',
        "停止当前进程")
    
    # 2. 创建简单的 watcher 脚本 - 分步骤
    run_command(ssh,
        'powershell -Command "Write-Host \\"创建基础变量...\\"" > D:\\VideoTranscode\\scripts\\watcher_new.ps1',
        "创建新脚本文件")
    
    # 3. 添加基础配置
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"# 视频转码监控服务\\""',
        "添加注释")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"\\$downloadsPath = \'D:\\VideoTranscode\\downloads\'\\""',
        "添加下载路径")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"\\$processingPath = \'D:\\VideoTranscode\\processing\'\\""',
        "添加处理路径")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"\\$logFile = \'D:\\VideoTranscode\\logs\\watcher.log\'\\""',
        "添加日志路径")
    
    # 4. 添加日志函数
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"function Write-Log { param(\\$Message) ; \\$timestamp = Get-Date -Format \'yyyy-MM-dd HH:mm:ss\' ; \\$logMessage = \'\\$timestamp - \\$Message\' ; Write-Host \\$logMessage ; Add-Content -Path \\$logFile -Value \\$logMessage }\\""',
        "添加日志函数")
    
    # 5. 添加启动信息
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"Write-Log \'=== Watcher 服务启动 ===\'\\""',
        "添加启动信息")
    
    # 6. 添加主循环
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"\\$processedCount = 0\\""',
        "添加计数器")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"while (\\$true) {\\""',
        "开始主循环")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"  \\$videoFiles = Get-ChildItem -Path \\$downloadsPath -Filter \'*.mp4\' -File | Where-Object { \\$_.Length -gt 1000 }\\""',
        "添加文件检测")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"  if (\\$videoFiles.Count -gt 0) {\\""',
        "检查文件数量")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"    Write-Log \'发现 \\$\\(\\$videoFiles.Count\\) 个待处理视频\'\\""',
        "记录发现文件")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"    foreach (\\$file in \\$videoFiles) {\\""',
        "开始处理循环")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      Write-Log \'开始处理: \\$\\(\\$file.Name\\)\'\\""',
        "记录开始处理")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      \\$processingFile = Join-Path \\$processingPath \\$file.Name\\""',
        "设置处理文件路径")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      Move-Item -Path \\$file.FullName -Destination \\$processingFile -Force\\""',
        "移动文件")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      Write-Log \'文件已移动到处理目录\'\\""',
        "记录移动完成")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      \\$result = & powershell -ExecutionPolicy Bypass -File \'D:\\VideoTranscode\\scripts\\transcode_full.ps1\' -InputFile \\$processingFile\\""',
        "调用转码脚本")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"      if (\\$LASTEXITCODE -eq 0) { Write-Log \'转码成功\' ; \\$processedCount++ } else { Write-Log \'转码失败\' }\\""',
        "处理转码结果")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"    }\\""',
        "结束处理循环")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"  }\\""',
        "结束文件检查")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"  Start-Sleep -Seconds 10\\""',
        "添加等待")
    
    run_command(ssh,
        'powershell -Command "Add-Content D:\\VideoTranscode\\scripts\\watcher_new.ps1 \\"}\\""',
        "结束主循环")
    
    # 7. 替换旧脚本
    run_command(ssh,
        'powershell -Command "Move-Item D:\\VideoTranscode\\scripts\\watcher.ps1 D:\\VideoTranscode\\scripts\\watcher_old.ps1 -Force; Move-Item D:\\VideoTranscode\\scripts\\watcher_new.ps1 D:\\VideoTranscode\\scripts\\watcher.ps1 -Force"',
        "替换脚本文件")
    
    # 8. 测试新脚本
    run_command(ssh,
        'powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Measure-Object -Line"',
        "检查脚本行数")
    
    # 9. 启动新服务
    run_command(ssh,
        'powershell -Command "Start-Process powershell -ArgumentList \\"-ExecutionPolicy\\", \\"Bypass\\", \\"-NoExit\\", \\"-File\\", \\"D:\\VideoTranscode\\scripts\\watcher.ps1\\" -WindowStyle Minimized"',
        "启动新服务")
    
    # 10. 等待并检查
    print("\n⏳ 等待20秒，观察处理情况...")
    import time
    time.sleep(20)
    
    run_command(ssh,
        'powershell -Command "Write-Host \'Downloads:\'; Get-ChildItem D:\\VideoTranscode\\downloads | Select-Object Name; Write-Host \'\\nProcessing:\'; Get-ChildItem D:\\VideoTranscode\\processing | Select-Object Name; Write-Host \'\\n最新日志:\'; Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 5"',
        "检查处理结果")
    
    print("\n" + "=" * 50)
    print("✅ 简单 Watcher 脚本创建完成!")
    
except Exception as e:
    print(f"❌ 创建失败: {e}")
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()