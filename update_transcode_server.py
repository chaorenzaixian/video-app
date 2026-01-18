# update_transcode_server.py - 更新转码服务器的上传服务
import paramiko
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print("连接到转码服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    print("连接成功!")
    
    sftp = ssh.open_sftp()
    
    # 上传更新后的upload_server.py
    print("\n上传更新后的 upload_server.py...")
    local_path = "scripts/upload_server.py"
    remote_path = "D:\\VideoTranscode\\scripts\\upload_server.py"
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('\r\n', '\n').replace('\n', '\r\n')
    
    with sftp.file(remote_path, 'w') as remote_file:
        remote_file.write(content)
    print(f"  完成: {remote_path}")
    
    sftp.close()
    
    # 停止旧服务
    print("\n停止旧的上传服务...")
    ssh.exec_command('powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"')
    time.sleep(2)
    
    # 重新启动服务
    print("重新启动上传服务...")
    stdin, stdout, stderr = ssh.exec_command(
        'schtasks /run /tn "TranscodeUploadServer"'
    )
    stdout.channel.recv_exit_status()
    
    time.sleep(5)
    
    # 验证服务
    print("\n验证服务...")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/health')
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"健康检查: {output}")
    
    ssh.close()
    
    if 'ok' in output.lower():
        print("\n✓ 上传服务更新成功!")
    else:
        print("\n✗ 服务可能未正常启动")

if __name__ == "__main__":
    main()
