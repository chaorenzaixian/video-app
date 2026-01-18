# run_upload_service_background.py - 在后台运行上传服务
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
    
    # 先杀掉可能存在的旧进程
    print("\n清理旧进程...")
    ssh.exec_command('powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"')
    time.sleep(2)
    
    # 创建一个VBS脚本来在后台运行Python
    print("\n创建后台启动脚本...")
    vbs_content = '''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python D:\\VideoTranscode\\scripts\\upload_server.py", 0, False
'''
    
    sftp = ssh.open_sftp()
    with sftp.file("D:\\VideoTranscode\\start_upload_hidden.vbs", 'w') as f:
        f.write(vbs_content)
    sftp.close()
    
    # 运行VBS脚本启动后台服务
    print("启动后台服务...")
    stdin, stdout, stderr = ssh.exec_command(
        'cscript //nologo D:\\VideoTranscode\\start_upload_hidden.vbs'
    )
    stdout.channel.recv_exit_status()
    
    # 等待服务启动
    time.sleep(3)
    
    # 检查服务状态
    print("\n检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"Python进程: {output.strip() if output.strip() else '未找到'}")
    
    # 检查端口
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "netstat -an | Select-String \':5000.*LISTEN\'"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"端口监听: {output.strip() if output.strip() else '未监听'}")
    
    # 测试健康检查
    print("\n测试健康检查...")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/health')
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"健康检查: {output}")
    
    ssh.close()
    
    print("\n" + "=" * 50)
    if output and 'ok' in output.lower():
        print("✓ 上传服务启动成功!")
        print(f"  服务地址: http://{TRANSCODE_SERVER}:5000")
    else:
        print("✗ 服务可能未正常启动，请手动检查")

if __name__ == "__main__":
    main()
