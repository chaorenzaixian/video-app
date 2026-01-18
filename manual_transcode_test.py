#!/usr/bin/env python3
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🧪 手动测试转码真实视频")
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
    
    # 1. 查找一个真实的视频文件
    print("📋 查找真实视频文件...")
    stdin, stdout, stderr = ssh.exec_command('''powershell -Command "
$file = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File | Where-Object { $_.Name -like '*萝莉*' } | Select-Object -First 1
if ($file) {
    Write-Host \\\"找到文件: $($file.Name)\\\"
    Write-Host \\\"大小: $([math]::Round($file.Length / 1MB, 2))MB\\\"
    Write-Host \\\"路径: $($file.FullName)\\\"
    
    # 检查文件是否是真正的视频
    Write-Host \\\"\\n检查视频信息...\\\"
    & ffprobe -v error -show_entries format=duration,format_name -of json $file.FullName 2>&1
} else {
    Write-Host \\\"未找到文件\\\"
}
"''', timeout=60)
    
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    print(output)
    
    # 2. 尝试手动转码（使用简单的命令）
    print("\n\n📋 尝试手动转码...")
    stdin, stdout, stderr = ssh.exec_command('''powershell -Command "
$file = Get-ChildItem D:\\VideoTranscode\\processing -Filter *.mp4 -File | Where-Object { $_.Name -like '*萝莉*' } | Select-Object -First 1
if ($file) {
    $output = \\\"D:\\VideoTranscode\\completed\\test_manual_transcode.mp4\\\"
    Write-Host \\\"输入: $($file.FullName)\\\"
    Write-Host \\\"输出: $output\\\"
    Write-Host \\\"\\n开始转码...\\\"
    
    # 使用简单的 CPU 转码命令
    $process = Start-Process -FilePath \\\"ffmpeg\\\" -ArgumentList \\\"-i\\\", $file.FullName, \\\"-c:v\\\", \\\"libx264\\\", \\\"-preset\\\", \\\"fast\\\", \\\"-crf\\\", \\\"23\\\", \\\"-c:a\\\", \\\"aac\\\", \\\"-y\\\", $output -NoNewWindow -Wait -PassThru
    
    Write-Host \\\"\\n退出码: $($process.ExitCode)\\\"
    
    if (Test-Path $output) {
        $outFile = Get-Item $output
        Write-Host \\\"✅ 转码成功!\\\"
        Write-Host \\\"输出文件大小: $([math]::Round($outFile.Length / 1MB, 2))MB\\\"
    } else {
        Write-Host \\\"❌ 转码失败\\\"
    }
} else {
    Write-Host \\\"未找到文件\\\"
}
"''', timeout=120)
    
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    print(output)
    if error:
        print(f"\n错误输出:\n{error[:500]}")
    
    print("\n" + "=" * 50)
    print("📊 测试完成")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
