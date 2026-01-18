#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 验证视频文件真实性")
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
    
    # 检查 processing 目录中的文件
    print("📋 检查 processing 目录中的文件...")
    stdin, stdout, stderr = ssh.exec_command('''powershell -Command "
$files = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File
foreach ($file in $files) {
    Write-Host \\\"\\n========================================\\\"
    Write-Host \\\"文件: $($file.Name)\\\"
    Write-Host \\\"大小: $([math]::Round($file.Length / 1KB, 2))KB\\\"
    Write-Host \\\"路径: $($file.FullName)\\\"
    
    # 读取文件头部字节
    Write-Host \\\"\\n文件头部（前20字节）:\\\"
    $bytes = [System.IO.File]::ReadAllBytes($file.FullName) | Select-Object -First 20
    $hex = ($bytes | ForEach-Object { $_.ToString(\\\"X2\\\") }) -join \\\" \\\"
    Write-Host \\\"  HEX: $hex\\\"
    
    # 尝试用 ffprobe 检查
    Write-Host \\\"\\nFFprobe 检查:\\\"
    & ffprobe -v error -show_entries format=format_name,duration -of json $file.FullName 2>&1 | Out-String
}
"''', timeout=60)
    
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(output)
    
    print("\n" + "=" * 50)
    print("📊 分析")
    print("=" * 50)
    print("\n💡 真正的 MP4 文件应该:")
    print("- 文件头部以 '00 00 00 xx 66 74 79 70' 开始")
    print("- FFprobe 能够识别格式和时长")
    print("- 文件大小通常 > 100KB")
    print("\n如果文件头部不是这个格式，说明不是真正的视频文件")
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
