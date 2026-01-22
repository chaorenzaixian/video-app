#!/usr/bin/env python3
import paramiko
import os
import time

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password)

# 检查文件内容
cmd = 'findstr "transcode/categories" D:\\VideoTranscode\\service\\web_ui.py'
stdin, stdout, stderr = client.exec_command(cmd)
result = stdout.read().decode('gbk', errors='ignore')
print(f"File content check: {result}")

# 启动服务
print("Starting service...")
cmd = 'cd /d D:\\VideoTranscode\\service && start "" python web_ui.py'
stdin, stdout, stderr = client.exec_command(cmd)
time.sleep(5)

# 检查服务是否启动
cmd = 'netstat -an | findstr "8080.*LISTEN"'
stdin, stdout, stderr = client.exec_command(cmd)
result = stdout.read().decode('gbk', errors='ignore')
print(f"Port 8080 LISTENING: {result}")

# 检查python进程
cmd = 'tasklist | findstr python'
stdin, stdout, stderr = client.exec_command(cmd)
result = stdout.read().decode('gbk', errors='ignore')
print(f"Python processes: {result}")

client.close()
print("Done!")
