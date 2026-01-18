#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 诊断 Watcher 问题")
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
    print("✅ 连接成功!\n")
    
    # 1. 检查进程
    print("📋 检查 PowerShell 进程...")
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq powershell.exe" /V', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    if 'powershell.exe' in output:
        lines = [l for l in output.split('\n') if 'powershell.exe' in l]
        print(f"  找到 {len(lines)} 个 PowerShell 进程")
        for line in lines[:3]:
            print(f"  {line[:100]}")
    else:
        print("  ❌ 未找到 PowerShell 进程")
    
    # 2. 查看 watcher 脚本
    print("\n📋 查看 watcher 脚本（前20行）...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-Object -First 20"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in output.split('\n'):
        print(f"  {line}")
    
    # 3. 查看日志文件
    print("\n📋 查看 watcher 日志（最新10行）...")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in output.split('\n'):
        print(f"  {line}")
    
    # 4. 手动测试 watcher 脚本的扫描逻辑
    print("\n📋 手动测试文件扫描...")
    stdin, stdout, stderr = ssh.exec_command('''powershell -Command "
$downloadsPath = 'D:\\VideoTranscode\\downloads'
Write-Host '扫描根目录和子目录...'
$videoFiles = Get-ChildItem -Path $downloadsPath -Filter '*.mp4' -File -Recurse | Where-Object { $_.Length -gt 1000 }
Write-Host '找到' $videoFiles.Count '个文件'
foreach ($file in $videoFiles) {
    Write-Host '  -' $file.FullName '(' ([math]::Round($file.Length / 1MB, 2)) 'MB)'
}
"''', timeout=60)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(output)
    
    print("\n" + "=" * 50)
    print("📊 诊断完成")
    
except Exception as e:
    print(f"❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
