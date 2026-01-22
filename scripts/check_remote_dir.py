"""检查远程目录"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查目录
print("检查D:\\VideoTranscode\\service目录...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\service')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查web_ui.py是否存在
print("\n检查web_ui.py...")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\service\\web_ui.py | findstr "def add_local"')
out = stdout.read().decode('utf-8', errors='ignore')
print(out if out else "未找到add_local函数")

# 检查端口
print("\n检查8080端口...")
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr ":8080"')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查python进程
print("\n检查python进程...")
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
