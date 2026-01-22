"""启动远程转码服务"""
import paramiko
import time

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 先杀掉旧进程
print("停止旧服务...")
ssh.exec_command('taskkill /F /IM python.exe 2>nul')
time.sleep(2)

# 启动新服务
print("启动服务...")
stdin, stdout, stderr = ssh.exec_command(
    'cd /d D:\\VideoTranscode\\service && start /B python web_ui.py > service.log 2>&1',
    timeout=10
)
time.sleep(3)

# 检查状态
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080.*LISTEN"')
listen = stdout.read().decode().strip()
print("端口监听:", listen or "无")

stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
proc = stdout.read().decode().strip()
print("Python进程:", proc or "无")

# 测试API
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/system')
api = stdout.read().decode().strip()
print("API响应:", api or "无")

# 检查index.html是否有标签功能
stdin, stdout, stderr = ssh.exec_command('findstr "tagsContainer" D:\\VideoTranscode\\service\\templates\\index.html')
tags = stdout.read().decode().strip()
print("标签功能:", "已添加" if tags else "未添加")

ssh.close()
