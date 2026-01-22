"""检查转码管理页面是否能正常访问"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查页面是否能访问
print('=== 检查页面访问 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s -o nul -w "%{http_code}" http://localhost:8080/')
http_code = stdout.read().decode()
print(f'首页HTTP状态码: {http_code}')

# 获取页面内容的前500字符
print('\n=== 页面内容预览 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/ | head -c 500')
content = stdout.read().decode('utf-8', errors='ignore')
print(content)

# 检查服务进程
print('\n=== 服务进程 ===')
stdin, stdout, stderr = ssh.exec_command('tasklist | findstr python')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查8080端口
print('\n=== 8080端口监听 ===')
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr 8080')
print(stdout.read().decode())

ssh.close()
