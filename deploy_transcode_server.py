#!/usr/bin/env python3
"""
转码服务器远程部署脚本
使用 paramiko 进行SSH密码认证连接
"""
import paramiko
import os
import sys
from pathlib import Path

# 转码服务器配置
TRANSCODE_SERVER = {
    "host": "198.176.60.121",
    "port": 22,
    "username": "Administrator",
    "password": "jCkMIjNlnSd7f6GM"
}

# 主服务器SSH密钥内容
SSH_KEY_CONTENT = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----"""

# 要部署的脚本文件
SCRIPTS_TO_DEPLOY = [
    ("scripts/transcode_full.ps1", "D:\\VideoTranscode\\scripts\\transcode_full.ps1"),
    ("scripts/upload_full.ps1", "D:\\VideoTranscode\\scripts\\upload_full.ps1"),
    ("scripts/watcher_full.ps1", "D:\\VideoTranscode\\scripts\\watcher.ps1"),
]

def create_ssh_client():
    """创建SSH连接"""
    print(f"[连接] 正在连接到 {TRANSCODE_SERVER['host']}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=TRANSCODE_SERVER["host"],
            port=TRANSCODE_SERVER["port"],
            username=TRANSCODE_SERVER["username"],
            password=TRANSCODE_SERVER["password"],
            timeout=30
        )
        print("[连接] ✓ 连接成功!")
        return client
    except Exception as e:
        print(f"[连接] ✗ 连接失败: {e}")
        return None

def exec_command(client, command, show_output=True):
    """执行远程命令"""
    stdin, stdout, stderr = client.exec_command(command, timeout=60)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if show_output and output:
        print(output)
    if error:
        print(f"[错误] {error}")
    
    return output, error

def create_directories(client):
    """创建目录结构"""
    print("\n[1/4] 创建目录结构...")
    
    dirs = [
        "D:\\VideoTranscode\\downloads",
        "D:\\VideoTranscode\\processing",
        "D:\\VideoTranscode\\completed",
        "D:\\VideoTranscode\\logs",
        "D:\\VideoTranscode\\scripts"
    ]
    
    for dir_path in dirs:
        cmd = f'powershell -Command "if (-not (Test-Path \'{dir_path}\')) {{ New-Item -ItemType Directory -Path \'{dir_path}\' -Force | Out-Null; Write-Host \'创建: {dir_path}\' }}"'
        exec_command(client, cmd)
    
    print("[1/4] ✓ 目录创建完成")

def create_ssh_key(client):
    """创建SSH密钥文件"""
    print("\n[2/4] 创建SSH密钥...")
    
    # 使用PowerShell创建密钥文件
    key_escaped = SSH_KEY_CONTENT.replace('"', '`"').replace('\n', '`n')
    cmd = f'''powershell -Command "$key = @'
{SSH_KEY_CONTENT}
'@
$key | Out-File -FilePath 'C:\\server_key' -Encoding ASCII -NoNewline
if (Test-Path 'C:\\server_key') {{ Write-Host '✓ SSH密钥已创建: C:\\server_key' }} else {{ Write-Host '✗ 创建失败' }}"'''
    
    exec_command(client, cmd)
    print("[2/4] ✓ SSH密钥创建完成")

def upload_scripts(client):
    """上传脚本文件"""
    print("\n[3/4] 上传脚本文件...")
    
    sftp = client.open_sftp()
    
    for local_path, remote_path in SCRIPTS_TO_DEPLOY:
        if os.path.exists(local_path):
            print(f"  上传: {local_path} -> {remote_path}")
            try:
                # Windows路径需要转换
                remote_path_unix = remote_path.replace("\\", "/")
                sftp.put(local_path, remote_path_unix)
                print(f"  ✓ {os.path.basename(local_path)}")
            except Exception as e:
                print(f"  ✗ 上传失败: {e}")
        else:
            print(f"  ✗ 本地文件不存在: {local_path}")
    
    sftp.close()
    print("[3/4] ✓ 脚本上传完成")

def verify_deployment(client):
    """验证部署"""
    print("\n[4/4] 验证部署...")
    
    # 检查文件
    cmd = 'powershell -Command "Get-ChildItem D:\\VideoTranscode\\scripts\\ | Select-Object Name, Length"'
    output, _ = exec_command(client, cmd)
    
    # 检查SSH密钥
    cmd = 'powershell -Command "if (Test-Path C:\\server_key) { Write-Host \'SSH密钥: 存在\' } else { Write-Host \'SSH密钥: 不存在\' }"'
    exec_command(client, cmd)
    
    # 测试SSH连接到主服务器
    print("\n  测试SSH连接到主服务器...")
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.47.218.137 "echo 连接成功"'
    output, error = exec_command(client, cmd)
    
    if "连接成功" in output:
        print("  ✓ SSH连接测试成功")
    else:
        print("  ✗ SSH连接测试失败")
    
    print("[4/4] ✓ 验证完成")

def main():
    print("=" * 50)
    print("  转码服务器远程部署")
    print("=" * 50)
    
    # 连接
    client = create_ssh_client()
    if not client:
        sys.exit(1)
    
    try:
        # 1. 创建目录
        create_directories(client)
        
        # 2. 创建SSH密钥
        create_ssh_key(client)
        
        # 3. 上传脚本
        upload_scripts(client)
        
        # 4. 验证
        verify_deployment(client)
        
        print("\n" + "=" * 50)
        print("  部署完成!")
        print("=" * 50)
        print("\n下一步: 在转码服务器上启动监控服务")
        print("命令: powershell -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()
