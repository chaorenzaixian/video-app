"""检查启动错误"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 杀掉旧进程
print("杀掉旧进程...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(2)

# 尝试导入web_ui
print("\n尝试导入web_ui...")
stdin, stdout, stderr = ssh.exec_command('D: && cd D:\\VideoTranscode\\service && python -c "import web_ui; print(web_ui)"')
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"输出: {out}")
if err:
    print(f"错误: {err}")

# 尝试运行
print("\n尝试运行web_ui.py...")
stdin, stdout, stderr = ssh.exec_command('D: && cd D:\\VideoTranscode\\service && python web_ui.py 2>&1', timeout=10)
time.sleep(5)
try:
    out = stdout.read().decode('utf-8', errors='ignore')
    print(f"输出: {out[:1000]}")
except:
    print("读取超时（可能正在运行）")

# 检查端口
print("\n检查端口...")
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
print(result if result else "未监听")

ssh.close()
