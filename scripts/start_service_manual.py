"""手动启动服务"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 先检查语法
print("检查语法...")
stdin, stdout, stderr = ssh.exec_command('cd D:\\VideoTranscode\\service && python -m py_compile web_ui.py')
err = stderr.read().decode('utf-8', errors='ignore')
if err:
    print(f"语法错误: {err}")
else:
    print("语法OK")

# 杀掉旧进程
print("\n杀掉旧进程...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# 启动服务
print("启动服务...")
cmd = 'start /b cmd /c "cd /d D:\\VideoTranscode\\service && python web_ui.py > service.log 2>&1"'
stdin, stdout, stderr = ssh.exec_command(cmd)
time.sleep(5)

# 检查
print("\n检查端口...")
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
print(result if result else "未监听")

# 检查日志
print("\n检查日志...")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\service\\service.log')
log = stdout.read().decode('utf-8', errors='ignore')
print(log[-1000:] if log else "无日志")

ssh.close()
