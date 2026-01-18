# verify_full_setup.py - 验证转码服务器完整配置
import paramiko

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def run_command(ssh, cmd, description):
    """运行命令并返回结果"""
    print(f"\n{description}...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    return output, error

def main():
    print("=" * 60)
    print("转码服务器配置验证")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    print("连接成功!")
    
    # 1. 检查目录结构
    output, _ = run_command(ssh, 
        'powershell -Command "Get-ChildItem D:\\VideoTranscode -Directory | Select-Object Name"',
        "1. 检查目录结构")
    print(output)
    
    # 2. 检查脚本文件
    output, _ = run_command(ssh,
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\scripts\\*.ps1 | Select-Object Name, Length"',
        "2. 检查脚本文件")
    print(output)
    
    # 3. 检查FFmpeg
    output, error = run_command(ssh,
        'powershell -Command "ffmpeg -version | Select-Object -First 1"',
        "3. 检查FFmpeg")
    print(output if output else error)
    
    # 4. 检查SSH密钥
    output, _ = run_command(ssh,
        'powershell -Command "if (Test-Path C:\\server_key) { \'SSH密钥存在\' } else { \'SSH密钥不存在\' }"',
        "4. 检查SSH密钥")
    print(output)
    
    # 5. 测试SSH连接到主服务器
    output, error = run_command(ssh,
        'powershell -Command "ssh -i C:\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@38.47.218.137 \'echo SSH连接成功\'"',
        "5. 测试SSH连接到主服务器")
    print(output if output else f"错误: {error}")
    
    # 6. 检查NVIDIA GPU
    output, error = run_command(ssh,
        'powershell -Command "nvidia-smi --query-gpu=name --format=csv,noheader 2>$null"',
        "6. 检查NVIDIA GPU")
    print(output if output else "未检测到NVIDIA GPU")
    
    # 7. 检查日志文件
    output, _ = run_command(ssh,
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\ | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize"',
        "7. 检查日志文件")
    print(output)
    
    ssh.close()
    
    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 在转码服务器上运行监控服务:")
    print("   powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\watcher.ps1")
    print("\n2. 将视频文件放入 D:\\VideoTranscode\\downloads\\ 目录")
    print("\n3. 监控服务会自动处理: 转码 → 生成封面 → 生成预览 → 上传到主服务器")

if __name__ == "__main__":
    main()
