"""运行并获取输出"""
import paramiko
import time
import select

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 杀掉旧进程
print("杀掉旧进程...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# 运行并捕获输出
print("\n运行web_ui.py...")
transport = ssh.get_transport()
channel = transport.open_session()
channel.exec_command('D: && cd D:\\VideoTranscode\\service && python web_ui.py')

# 等待并读取输出
start = time.time()
output = ""
while time.time() - start < 15:
    if channel.recv_ready():
        data = channel.recv(4096).decode('utf-8', errors='ignore')
        output += data
        print(data, end='')
    if channel.recv_stderr_ready():
        data = channel.recv_stderr(4096).decode('utf-8', errors='ignore')
        output += data
        print("STDERR:", data, end='')
    if channel.exit_status_ready():
        break
    time.sleep(0.5)

print("\n\n--- 输出结束 ---")

# 检查端口
print("\n检查端口...")
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
print(result if result else "未监听")

ssh.close()
