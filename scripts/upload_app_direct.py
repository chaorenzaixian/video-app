"""
直接通过 SSH 上传 APK 和 mobileconfig 文件到服务器
"""
import os
import paramiko
from scp import SCPClient

# 服务器配置
SERVER_HOST = "38.47.218.230"
SERVER_USER = "root"
SERVER_KEY = "server_key_main"
UPLOAD_DIR = "/www/wwwroot/app-download"

def create_ssh_client():
    """创建 SSH 连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 使用密钥文件连接
    key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), SERVER_KEY)
    
    print(f"连接服务器 {SERVER_HOST}...")
    ssh.connect(
        hostname=SERVER_HOST,
        username=SERVER_USER,
        key_filename=key_path,
        timeout=30
    )
    print("连接成功！")
    return ssh

def upload_file(ssh, local_path, remote_filename):
    """上传文件到服务器"""
    if not os.path.exists(local_path):
        print(f"文件不存在: {local_path}")
        return False
    
    file_size = os.path.getsize(local_path)
    print(f"上传文件: {local_path}")
    print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
    
    remote_path = f"{UPLOAD_DIR}/{remote_filename}"
    
    # 确保目录存在
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {UPLOAD_DIR}")
    stdout.read()
    
    # 使用 SCP 上传
    with SCPClient(ssh.get_transport(), progress=progress_callback) as scp:
        scp.put(local_path, remote_path)
    
    # 设置权限
    ssh.exec_command(f"chmod 644 {remote_path}")
    
    print(f"\n上传完成: {remote_path}")
    print(f"下载地址: http://{SERVER_HOST}/{remote_filename}")
    return True

def progress_callback(filename, size, sent):
    """上传进度回调"""
    percent = sent / size * 100
    bar_len = 40
    filled = int(bar_len * sent / size)
    bar = '=' * filled + '-' * (bar_len - filled)
    print(f"\r[{bar}] {percent:.1f}%", end='', flush=True)

def main():
    print("=" * 50)
    print("App 文件直接上传工具 (SSH)")
    print("=" * 50)
    
    # 文件路径
    apk_path = "flutter/build/app/outputs/flutter-apk/app-release.apk"
    mobileconfig_path = "packages/Soul.mobileconfig"
    
    try:
        ssh = create_ssh_client()
        
        # 上传 APK
        print("\n--- 上传 APK ---")
        if os.path.exists(apk_path):
            upload_file(ssh, apk_path, "Soul.apk")
        else:
            print(f"APK 文件不存在: {apk_path}")
        
        # 上传 mobileconfig
        print("\n--- 上传 Mobileconfig ---")
        if os.path.exists(mobileconfig_path):
            upload_file(ssh, mobileconfig_path, "Soul.mobileconfig")
        else:
            print(f"Mobileconfig 文件不存在: {mobileconfig_path}")
        
        # 列出上传目录内容
        print("\n--- 服务器文件列表 ---")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {UPLOAD_DIR}")
        print(stdout.read().decode())
        
        ssh.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    print("\n下载地址:")
    print(f"  APK: http://{SERVER_HOST}/Soul.apk")
    print(f"  Mobileconfig: http://{SERVER_HOST}/Soul.mobileconfig")

if __name__ == "__main__":
    main()
