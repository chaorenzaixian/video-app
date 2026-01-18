#!/usr/bin/env python3
"""验证转码服务器完整配置"""
import paramiko
import time

TRANSCODE_SERVER = {
    "host": "198.176.60.121",
    "port": 22,
    "username": "Administrator",
    "password": "jCkMIjNlnSd7f6GM"
}

def main():
    print("=" * 60)
    print("  转码服务器配置验证")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=TRANSCODE_SERVER["host"],
        port=TRANSCODE_SERVER["port"],
        username=TRANSCODE_SERVER["username"],
        password=TRANSCODE_SERVER["password"],
        timeout=30
    )
    print("✓ 连接成功\n")
    
    # 1. 检查目录结构
    print("[1] 目录结构")
    stdin, stdout, stderr = client.exec_command('dir D:\\VideoTranscode', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    
    required_dirs = ['downloads', 'processing', 'completed', 'logs', 'scripts']
    for d in required_dirs:
        if d in output:
            print(f"  ✓ {d}/")
        else:
            print(f"  ✗ {d}/ (缺失)")
    
    # 2. 检查脚本文件
    print("\n[2] 脚本文件")
    stdin, stdout, stderr = client.exec_command('dir D:\\VideoTranscode\\scripts\\*.ps1', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    
    required_scripts = ['transcode_full.ps1', 'upload_full.ps1', 'watcher.ps1']
    for s in required_scripts:
        if s in output:
            print(f"  ✓ {s}")
        else:
            print(f"  ✗ {s} (缺失)")
    
    # 3. 检查SSH密钥
    print("\n[3] SSH密钥")
    stdin, stdout, stderr = client.exec_command('if exist C:\\server_key (echo EXISTS) else (echo MISSING)', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    if 'EXISTS' in output:
        print("  ✓ C:\\server_key 存在")
    else:
        print("  ✗ C:\\server_key 缺失")
    
    # 4. 检查FFmpeg
    print("\n[4] FFmpeg")
    stdin, stdout, stderr = client.exec_command('ffmpeg -version 2>&1 | findstr "ffmpeg version"', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    if 'ffmpeg version' in output:
        print(f"  ✓ {output.strip()}")
    else:
        print("  ✗ FFmpeg 未安装或不在PATH中")
    
    # 5. 检查GPU
    print("\n[5] GPU (NVIDIA)")
    stdin, stdout, stderr = client.exec_command('nvidia-smi --query-gpu=name --format=csv,noheader 2>&1', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    if 'NVIDIA' in output or 'GeForce' in output or 'Tesla' in output or 'RTX' in output:
        print(f"  ✓ {output.strip()}")
    else:
        print("  ⚠ 未检测到NVIDIA GPU (将使用CPU转码)")
    
    # 6. 测试SSH到主服务器
    print("\n[6] SSH连接到主服务器")
    stdin, stdout, stderr = client.exec_command(
        'ssh -i C:\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@38.47.218.137 "echo OK" 2>&1',
        timeout=15
    )
    time.sleep(8)
    if stdout.channel.recv_ready():
        output = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if 'OK' in output:
            print("  ✓ SSH连接成功")
        else:
            print(f"  ✗ SSH连接失败: {output[:100]}")
    else:
        print("  ⚠ SSH测试超时")
    
    # 7. 磁盘空间
    print("\n[7] 磁盘空间")
    stdin, stdout, stderr = client.exec_command('wmic logicaldisk get size,freespace,caption 2>&1', timeout=10)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"  {output.strip()}")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("  验证完成!")
    print("=" * 60)
    print("\n下一步: 启动监控服务")
    print("  1. 远程桌面连接到 198.176.60.121")
    print("  2. 打开 PowerShell (管理员)")
    print("  3. 执行:")
    print("     powershell -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1")
    print("\n或者手动测试转码:")
    print("  1. 将视频文件放入 D:\\VideoTranscode\\downloads\\")
    print("  2. 监控服务会自动处理")

if __name__ == "__main__":
    main()
