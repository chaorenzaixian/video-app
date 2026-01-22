"""立即启动服务"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 杀掉旧进程
print("杀掉旧进程...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# 使用wmic启动
print("启动服务...")
cmd = 'wmic process call create "cmd /c D: && cd D:\\VideoTranscode\\service && python web_ui.py"'
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('gbk', errors='ignore')
print(out)

# 等待
print("等待启动...")
time.sleep(8)

# 检查端口
print("\n检查端口...")
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
print(result if result else "未监听")

# 检查进程
print("\n检查进程...")
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
