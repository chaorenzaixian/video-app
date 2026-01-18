# setup_upload_service_task.py - 使用计划任务运行上传服务
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
    
    # 创建批处理启动脚本
    print("\n创建启动脚本...")
    bat_content = '''@echo off
cd /d D:\\VideoTranscode\\scripts
python upload_server.py > D:\\VideoTranscode\\logs\\upload_server.log 2>&1
'''
    sftp = ssh.open_sftp()
    with sftp.file("D:\\VideoTranscode\\run_upload_server.bat", 'w') as f:
        f.write(bat_content)
    sftp.close()
    
    # 删除旧的计划任务（如果存在）
    print("配置计划任务...")
    ssh.exec_command('schtasks /delete /tn "TranscodeUploadServer" /f 2>nul')
    time.sleep(1)
    
    # 创建计划任务（开机自启动）
    stdin, stdout, stderr = ssh.exec_command(
        'schtasks /create /tn "TranscodeUploadServer" /tr "D:\\VideoTranscode\\run_upload_server.bat" /sc onstart /ru SYSTEM /rl HIGHEST /f'
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    print(f"创建任务: {output or error}")
    
    # 立即运行任务
    print("\n启动服务...")
    stdin, stdout, stderr = ssh.exec_command(
        'schtasks /run /tn "TranscodeUploadServer"'
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"运行任务: {output}")
    
    # 等待启动
    time.sleep(5)
    
    # 检查状态
    print("\n检查服务状态...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Get-Process python -ErrorAction SilentlyContinue"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"Python进程: {'运行中' if output.strip() else '未运行'}")
    
    # 测试
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5000/health')
    output = stdout.read().decode('utf-8', errors='ignore')
    print(f"健康检查: {output}")
    
    ssh.close()
    
    if output and 'ok' in output.lower():
        print(f"\n✓ 上传服务启动成功! 地址: http://{TRANSCODE_SERVER}:5000")
    else:
        print("\n服务可能需要手动启动，请登录转码服务器运行:")
        print("  python D:\\VideoTranscode\\scripts\\upload_server.py")

if __name__ == "__main__":
    main()
