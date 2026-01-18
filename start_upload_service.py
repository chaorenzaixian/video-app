# start_upload_service.py - 在转码服务器上启动上传服务
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
    
    # 检查是否已经在运行
    print("\n检查上传服务状态...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like \'*upload_server*\' }"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    
    if 'python' in output.lower():
        print("上传服务已在运行")
    else:
        print("启动上传服务...")
        # 使用Start-Process在后台启动
        stdin, stdout, stderr = ssh.exec_command(
            'powershell -Command "Start-Process python -ArgumentList \'D:\\VideoTranscode\\scripts\\upload_server.py\' -WindowStyle Hidden"'
        )
        stdout.channel.recv_exit_status()
        time.sleep(3)
        print("上传服务已启动")
    
    # 测试服务
    print("\n测试上传服务...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Invoke-RestMethod -Uri \'http://localhost:5000/health\' -Method GET"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if 'ok' in output.lower() or 'status' in output.lower():
        print(f"服务正常: {output.strip()}")
    else:
        print(f"服务响应: {output}")
        if error:
            print(f"错误: {error}")
    
    ssh.close()
    print(f"\n上传服务地址: http://{TRANSCODE_SERVER}:5000")

if __name__ == "__main__":
    main()
