#!/usr/bin/env python3
"""
诊断转码错误
"""
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 诊断转码错误")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    
    # 1. 查看完整的转码日志
    print("📝 转码日志（最新30行）:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\transcode.log -Tail 30"', timeout=30)
    log = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in log.split('\n'):
        if line.strip():
            print(f"  {line}")
    
    # 2. 查看 processing 目录的文件
    print("\n📁 Processing 目录文件:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\*.mp4', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    print(files)
    
    # 3. 测试 FFmpeg 是否可用
    print("\n🔧 测试 FFmpeg:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('ffmpeg -version', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(output[:500])
    
    # 4. 测试 FFprobe 检测第一个文件
    print("\n🎬 测试 FFprobe 检测文件:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "$f = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 | Select-Object -First 1; if ($f) { Write-Host \'File:\' $f.FullName; Write-Host \'Size:\' $f.Length; & ffprobe -v error -show_entries format=duration -of csv=p=0 $f.FullName 2>&1 }"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(output)
    
    # 5. 手动测试转码第一个文件
    print("\n🎬 手动测试转码:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "$f = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 | Select-Object -First 1; if ($f) { $input = $f.FullName; $output = Join-Path \'D:\\VideoTranscode\\completed\\short\' (\'test_\' + $f.Name); Write-Host \'Input:\' $input; Write-Host \'Output:\' $output; & ffmpeg -i $input -c:v h264_nvenc -preset fast -b:v 2M -c:a aac -b:a 128k -y $output 2>&1 | Select-Object -Last 20 }"', timeout=120)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    print("输出:")
    for line in output.split('\n')[-20:]:
        if line.strip():
            print(f"  {line}")
    
    if error:
        print("\n错误:")
        for line in error.split('\n')[-10:]:
            if line.strip():
                print(f"  {line}")
    
    # 6. 检查转码脚本内容
    print("\n📄 转码脚本关键部分:")
    print("-" * 60)
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\transcode_full.ps1 | Select-Object -Skip 50 -First 30"', timeout=30)
    script = stdout.read().decode('utf-8', errors='ignore').strip()
    for line in script.split('\n'):
        if line.strip():
            print(f"  {line}")
    
except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
