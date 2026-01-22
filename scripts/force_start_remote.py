"""强制启动远程服务"""
import paramiko
import time

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 创建启动脚本
start_script = '''
@echo off
cd /d D:\\VideoTranscode\\service
python web_ui.py
'''

# 写入启动脚本
sftp = ssh.open_sftp()
with sftp.file('D:/VideoTranscode/service/start_web.bat', 'w') as f:
    f.write(start_script)
sftp.close()

# 使用schtasks创建一次性任务来启动
print("创建启动任务...")
ssh.exec_command('schtasks /delete /tn "StartWebUI" /f 2>nul')
time.sleep(1)

stdin, stdout, stderr = ssh.exec_command(
    'schtasks /create /tn "StartWebUI" /tr "D:\\VideoTranscode\\service\\start_web.bat" /sc once /st 00:00 /ru Administrator /rp jCkMIjNlnSd7f6GM /f'
)
print(stdout.read().decode('gbk', errors='ignore'))
print(stderr.read().decode('gbk', errors='ignore'))

stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "StartWebUI"')
print(stdout.read().decode('gbk', errors='ignore'))
print(stderr.read().decode('gbk', errors='ignore'))

time.sleep(5)

# 检查状态
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080.*LISTEN"')
listen = stdout.read().decode().strip()
print("端口监听:", listen or "无")

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/system')
api = stdout.read().decode().strip()
print("API响应:", api or "无")

ssh.close()
