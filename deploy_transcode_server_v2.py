#!/usr/bin/env python3
"""
转码服务器远程部署脚本 v2
使用 paramiko 进行SSH密码认证连接
"""
import paramiko
import os
import sys
import time

# 转码服务器配置
TRANSCODE_SERVER = {
    "host": "198.176.60.121",
    "port": 22,
    "username": "Administrator",
    "password": "jCkMIjNlnSd7f6GM"
}

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

def exec_command(client, command, timeout=30):
    """执行远程命令"""
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        return output, error
    except Exception as e:
        return "", str(e)

def create_ssh_key_via_sftp(client):
    """通过SFTP直接创建SSH密钥文件"""
    print("\n[创建SSH密钥]...")
    
    ssh_key_content = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gAAAAJDvzGZC78xm
QgAAAAtzc2gtZWQyNTUxOQAAACBE9vQLi1nGfWBVacAymJd/B6TeSVq6KeYxZBCd57L9gA
AAAECtAxcJq0SjnZjz4DYebdKR/2BX09k3EOCZniP9JI0SwkT29AuLWcZ9YFVpwDKYl38H
pN5JWrop5jFkEJ3nsv2AAAAADXJvb3RASEIxMzExMDM=
-----END OPENSSH PRIVATE KEY-----"""
    
    sftp = client.open_sftp()
    
    try:
        # 直接写入文件
        with sftp.file('/server_key', 'w') as f:
            f.write(ssh_key_content)
        print("  ✓ 创建 C:\\server_key")
        
        # 复制到C盘根目录
        exec_command(client, 'copy /Y C:\\Users\\Administrator\\server_key C:\\server_key 2>nul', timeout=10)
        
    except Exception as e:
        print(f"  尝试备用方法...")
        # 备用方法：写入用户目录
        try:
            with sftp.file('server_key', 'w') as f:
                f.write(ssh_key_content)
            # 移动到C盘
            exec_command(client, 'move /Y server_key C:\\server_key', timeout=10)
            print("  ✓ 创建 C:\\server_key (备用方法)")
        except Exception as e2:
            print(f"  ✗ 创建失败: {e2}")
    
    sftp.close()

def verify_files(client):
    """验证文件"""
    print("\n[验证文件]...")
    
    # 检查脚本文件
    output, _ = exec_command(client, 'dir D:\\VideoTranscode\\scripts\\*.ps1', timeout=10)
    print(output)
    
    # 检查SSH密钥
    output, _ = exec_command(client, 'if exist C:\\server_key (echo SSH密钥: 存在) else (echo SSH密钥: 不存在)', timeout=10)
    print(output)
    
    # 检查目录
    output, _ = exec_command(client, 'dir D:\\VideoTranscode', timeout=10)
    print(output)

def test_ssh_to_main(client):
    """测试SSH连接到主服务器"""
    print("\n[测试SSH连接到主服务器]...")
    print("  (这可能需要几秒钟...)")
    
    # 使用较短的超时
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes root@38.47.218.137 "echo OK" 2>&1'
    
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
        time.sleep(8)  # 等待命令执行
        
        # 非阻塞读取
        if stdout.channel.recv_ready():
            output = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            if 'OK' in output:
                print("  ✓ SSH连接成功!")
                return True
            else:
                print(f"  输出: {output}")
        
        if stdout.channel.recv_stderr_ready():
            error = stdout.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
            print(f"  错误: {error}")
        
    except Exception as e:
        print(f"  测试超时或失败: {e}")
    
    print("  ⚠ SSH测试未完成，请手动验证")
    return False

def main():
    print("=" * 50)
    print("  转码服务器部署验证")
    print("=" * 50)
    
    client = create_ssh_client()
    if not client:
        sys.exit(1)
    
    try:
        # 创建SSH密钥
        create_ssh_key_via_sftp(client)
        
        # 验证文件
        verify_files(client)
        
        # 测试SSH（可选）
        # test_ssh_to_main(client)
        
        print("\n" + "=" * 50)
        print("  部署完成!")
        print("=" * 50)
        print("\n已部署的文件:")
        print("  - D:\\VideoTranscode\\scripts\\transcode_full.ps1")
        print("  - D:\\VideoTranscode\\scripts\\upload_full.ps1")
        print("  - D:\\VideoTranscode\\scripts\\watcher.ps1")
        print("  - C:\\server_key")
        print("\n下一步操作:")
        print("  1. 远程桌面连接到 198.176.60.121")
        print("  2. 打开 PowerShell")
        print("  3. 运行: powershell -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()
