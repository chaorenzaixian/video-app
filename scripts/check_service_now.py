"""检查服务状态"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 等待
time.sleep(3)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
print('端口检查:')
print(result if result else '未监听')

# 检查进程
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print('\nPython进程:')
print(stdout.read().decode('gbk', errors='ignore'))

# 测试API
import urllib.request
try:
    req = urllib.request.Request("http://198.176.60.121:8080/api/system")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('\nAPI响应:')
        print(resp.read().decode())
except Exception as e:
    print(f'\nAPI错误: {e}')

ssh.close()
