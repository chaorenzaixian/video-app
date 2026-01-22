"""检查转码服务状态"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080.*LISTEN"')
print("端口监听:", stdout.read().decode().strip() or "无")

# 检查进程
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print("Python进程:", stdout.read().decode().strip() or "无")

# 检查web_ui.py是否有add-local
stdin, stdout, stderr = ssh.exec_command('findstr "add-local" D:\\VideoTranscode\\service\\web_ui.py')
print("add-local路由:", stdout.read().decode().strip() or "无")

# 尝试本地访问
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/system')
print("本地API响应:", stdout.read().decode().strip() or "无响应")

ssh.close()
