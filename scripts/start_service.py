"""启动转码服务"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 杀掉现有进程
print("停止现有服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(3)

# 启动服务
print("启动服务...")
cmd = 'wmic process call create "cmd /c D: & cd D:\\VideoTranscode\\service & python web_ui.py"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('gbk', errors='ignore'))

# 等待启动
print("等待启动...")
time.sleep(15)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务未监听")
    # 检查进程
    stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
    print("Python进程:", stdout.read().decode('gbk', errors='ignore'))

ssh.close()
