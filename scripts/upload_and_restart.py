"""上传文件并重启服务"""
import paramiko
import time

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

sftp = ssh.open_sftp()

# 上传文件（使用二进制模式确保编码正确）
files = [
    ('transcode_service/web_ui.py', 'D:/VideoTranscode/service/web_ui.py'),
    ('transcode_service/templates/index.html', 'D:/VideoTranscode/service/templates/index.html'),
]

for local, remote in files:
    try:
        # 读取本地文件内容
        with open(local, 'rb') as f:
            content = f.read()
        # 写入远程文件
        with sftp.file(remote, 'wb') as f:
            f.write(content)
        print(f"✓ {local} ({len(content)} bytes)")
    except Exception as e:
        print(f"✗ {local}: {e}")

sftp.close()

# 检查语法
print("\n检查语法...")
stdin, stdout, stderr = ssh.exec_command('D: & cd D:\\VideoTranscode\\service & python -m py_compile web_ui.py', timeout=30)
err = stderr.read().decode('gbk', errors='ignore')
if err:
    print("语法错误:", err)
else:
    print("语法正确")

# 重启服务
print("\n重启服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

cmd = 'wmic process call create "cmd /c D: & cd D:\\VideoTranscode\\service & python web_ui.py"'
ssh.exec_command(cmd)
time.sleep(8)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务未监听，等待更长时间...")
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
    result = stdout.read().decode('gbk', errors='ignore')
    if 'LISTENING' in result:
        print("✓ 服务已启动")
    else:
        print("✗ 服务启动失败")

ssh.close()
print("完成!")
