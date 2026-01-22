"""上传所有文件"""
import paramiko
import time

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

sftp = ssh.open_sftp()

# 上传文件列表
files = [
    ('transcode_service/web_ui.py', 'D:/VideoTranscode/service/web_ui.py'),
    ('transcode_service/templates/index.html', 'D:/VideoTranscode/service/templates/index.html'),
    ('transcode_service/config.py', 'D:/VideoTranscode/service/config.py'),
    ('transcode_service/task_queue.py', 'D:/VideoTranscode/service/task_queue.py'),
    ('transcode_service/uploader.py', 'D:/VideoTranscode/service/uploader.py'),
]

for local, remote in files:
    try:
        sftp.put(local, remote)
        print(f"✓ {local}")
    except Exception as e:
        print(f"✗ {local}: {e}")

sftp.close()

# 重启服务
print("\n重启服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

cmd = 'wmic process call create "cmd /c D: && cd D:\\VideoTranscode\\service && python web_ui.py"'
ssh.exec_command(cmd)
time.sleep(8)

# 检查
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')

if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务启动失败")

ssh.close()
print("完成!")
