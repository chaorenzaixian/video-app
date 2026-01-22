"""直接启动服务"""
import paramiko
import time

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 使用pythonw后台运行
print("启动服务...")
channel = ssh.get_transport().open_session()
channel.exec_command('cd /d D:\\VideoTranscode\\service && pythonw -c "exec(open(\'web_ui.py\').read())"')

time.sleep(5)

# 检查状态
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080.*LISTEN"')
listen = stdout.read().decode().strip()
print("端口监听:", listen or "无")

if not listen:
    # 尝试用python直接运行
    print("\n尝试用python运行...")
    channel2 = ssh.get_transport().open_session()
    channel2.exec_command('cd /d D:\\VideoTranscode\\service && start "" python web_ui.py')
    time.sleep(5)
    
    stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080.*LISTEN"')
    listen = stdout.read().decode().strip()
    print("端口监听:", listen or "无")

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/system')
api = stdout.read().decode().strip()
print("API响应:", api or "无")

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/tags')
tags = stdout.read().decode().strip()
print("标签API:", tags[:200] if tags else "无")

ssh.close()
