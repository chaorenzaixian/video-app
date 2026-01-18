# deploy_upload_server.py - 部署上传服务到转码服务器
import paramiko
import os

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print("=" * 50)
    print("部署上传服务到转码服务器")
    print("=" * 50)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    print("连接成功!")
    
    sftp = ssh.open_sftp()
    
    # 1. 上传upload_server.py
    print("\n1. 上传 upload_server.py...")
    local_path = "scripts/upload_server.py"
    remote_path = "D:\\VideoTranscode\\scripts\\upload_server.py"
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('\r\n', '\n').replace('\n', '\r\n')
    
    with sftp.file(remote_path, 'w') as remote_file:
        remote_file.write(content)
    print(f"  完成: {remote_path}")
    
    # 2. 安装依赖
    print("\n2. 安装Python依赖...")
    stdin, stdout, stderr = ssh.exec_command(
        'pip install flask flask-cors werkzeug'
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "  依赖已安装")
    
    # 3. 创建启动脚本
    print("\n3. 创建启动脚本...")
    start_script = '''@echo off
echo Starting Upload Server...
cd /d D:\\VideoTranscode\\scripts
python upload_server.py
pause
'''
    with sftp.file("D:\\VideoTranscode\\start_upload_server.bat", 'w') as f:
        f.write(start_script)
    print("  完成: D:\\VideoTranscode\\start_upload_server.bat")
    
    # 4. 检查防火墙（提示）
    print("\n4. 防火墙配置...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "New-NetFirewallRule -DisplayName \'Transcode Upload Server\' -Direction Inbound -Port 5000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue"'
    )
    stdout.channel.recv_exit_status()
    print("  已添加防火墙规则 (端口5000)")
    
    sftp.close()
    ssh.close()
    
    print("\n" + "=" * 50)
    print("部署完成!")
    print("=" * 50)
    print("\n启动方式:")
    print("  1. 登录转码服务器")
    print("  2. 双击运行 D:\\VideoTranscode\\start_upload_server.bat")
    print("  或者运行: python D:\\VideoTranscode\\scripts\\upload_server.py")
    print(f"\n服务地址: http://{TRANSCODE_SERVER}:5000")

if __name__ == "__main__":
    main()
