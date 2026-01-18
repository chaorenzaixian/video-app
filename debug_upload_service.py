# debug_upload_service.py - 调试上传服务
import paramiko

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print("连接到转码服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    print("连接成功!")
    
    # 检查Python版本
    print("\n检查Python...")
    stdin, stdout, stderr = ssh.exec_command('python --version')
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(f"Python: {output or error}")
    
    # 检查脚本是否存在
    print("\n检查脚本文件...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Test-Path D:\\VideoTranscode\\scripts\\upload_server.py"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"脚本存在: {output.strip()}")
    
    # 尝试直接运行并捕获错误
    print("\n尝试运行脚本（5秒后超时）...")
    stdin, stdout, stderr = ssh.exec_command(
        'python D:\\VideoTranscode\\scripts\\upload_server.py 2>&1',
        timeout=10
    )
    
    # 等待几秒看输出
    import time
    time.sleep(5)
    
    # 读取输出
    try:
        stdout.channel.settimeout(2)
        output = ""
        while True:
            try:
                chunk = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                if not chunk:
                    break
                output += chunk
            except:
                break
        print(f"输出:\n{output}")
    except Exception as e:
        print(f"读取输出异常: {e}")
    
    ssh.close()

if __name__ == "__main__":
    main()
