#!/usr/bin/env python3
"""
部署Python转码服务到Windows转码服务器
"""
import os
import paramiko
import zipfile
import tempfile
from io import BytesIO

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"
REMOTE_DIR = r"D:\VideoTranscode\service"

# 要上传的文件
SERVICE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "transcode_service")

def deploy():
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    sftp = ssh.open_sftp()
    
    # 创建远程目录
    print(f"创建目录 {REMOTE_DIR}...")
    stdin, stdout, stderr = ssh.exec_command(f'if not exist "{REMOTE_DIR}" mkdir "{REMOTE_DIR}"')
    stdout.read()
    stdin, stdout, stderr = ssh.exec_command(f'if not exist "{REMOTE_DIR}\\templates" mkdir "{REMOTE_DIR}\\templates"')
    stdout.read()
    stdin, stdout, stderr = ssh.exec_command(f'if not exist "{REMOTE_DIR}\\static" mkdir "{REMOTE_DIR}\\static"')
    stdout.read()
    
    # 上传文件
    files_to_upload = [
        "config.py",
        "task_queue.py",
        "transcoder.py",
        "uploader.py",
        "callback.py",
        "worker.py",
        "web_ui.py",
        "service.py",
        "requirements.txt",
    ]
    
    for filename in files_to_upload:
        local_path = os.path.join(SERVICE_DIR, filename)
        remote_path = f"{REMOTE_DIR}\\{filename}"
        
        if os.path.exists(local_path):
            print(f"上传 {filename}...")
            sftp.put(local_path, remote_path)
        else:
            print(f"跳过 {filename} (不存在)")
    
    # 上传模板
    templates_dir = os.path.join(SERVICE_DIR, "templates")
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            local_path = os.path.join(templates_dir, filename)
            remote_path = f"{REMOTE_DIR}\\templates\\{filename}"
            print(f"上传 templates/{filename}...")
            sftp.put(local_path, remote_path)
    
    sftp.close()
    
    # 安装依赖
    print("\n安装Python依赖...")
    stdin, stdout, stderr = ssh.exec_command(f'cd /d "{REMOTE_DIR}" && pip install -r requirements.txt')
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print(f"警告: {err}")
    
    # 创建启动脚本
    print("\n创建启动脚本...")
    start_script = f'''@echo off
cd /d "{REMOTE_DIR}"
python service.py
pause
'''
    stdin, stdout, stderr = ssh.exec_command(f'echo {start_script} > "{REMOTE_DIR}\\start.bat"')
    stdout.read()
    
    # 创建启动脚本（后台运行）
    start_bg_script = f'''@echo off
cd /d "{REMOTE_DIR}"
start /B pythonw service.py
echo 服务已在后台启动
echo Web管理界面: http://localhost:8080
'''
    cmd = f'''powershell -Command "Set-Content -Path '{REMOTE_DIR}\\start_background.bat' -Value @'
@echo off
cd /d {REMOTE_DIR}
start /B python service.py
echo Service started in background
echo Web UI: http://localhost:8080
'@"'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    stdout.read()
    
    ssh.close()
    
    print("\n" + "="*50)
    print("部署完成！")
    print("="*50)
    print(f"\n服务目录: {REMOTE_DIR}")
    print("\n启动方式:")
    print(f"  1. 前台运行: {REMOTE_DIR}\\start.bat")
    print(f"  2. 后台运行: {REMOTE_DIR}\\start_background.bat")
    print(f"  3. 命令行: cd {REMOTE_DIR} && python service.py")
    print("\nWeb管理界面: http://198.176.60.121:8080")


def test_service():
    """测试服务是否运行"""
    print(f"\n检查服务状态...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 检查Python进程
    stdin, stdout, stderr = ssh.exec_command('tasklist /FI "IMAGENAME eq python.exe"')
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)
    
    # 检查端口
    stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr ":8080"')
    output = stdout.read().decode('utf-8', errors='replace')
    if output.strip():
        print("✓ 端口8080已监听")
        print(output)
    else:
        print("✗ 端口8080未监听")
    
    ssh.close()


def start_service():
    """启动服务"""
    print(f"\n启动转码服务...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 先停止旧进程
    print("停止旧进程...")
    stdin, stdout, stderr = ssh.exec_command('taskkill /F /IM python.exe /FI "WINDOWTITLE eq *service*" 2>nul')
    stdout.read()
    
    # 启动新进程
    print("启动服务...")
    cmd = f'start /B cmd /c "cd /d {REMOTE_DIR} && python service.py > service.log 2>&1"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    import time
    time.sleep(3)
    
    # 检查是否启动成功
    stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr ":8080"')
    output = stdout.read().decode('utf-8', errors='replace')
    
    ssh.close()
    
    if output.strip():
        print("\n✓ 服务启动成功！")
        print(f"Web管理界面: http://{TRANSCODE_HOST}:8080")
    else:
        print("\n✗ 服务可能未启动，请检查日志")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test":
            test_service()
        elif cmd == "start":
            start_service()
        else:
            print("用法:")
            print("  python deploy_transcode_service.py        - 部署服务")
            print("  python deploy_transcode_service.py test   - 测试服务状态")
            print("  python deploy_transcode_service.py start  - 启动服务")
    else:
        deploy()
