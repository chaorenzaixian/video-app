"""检查服务启动错误"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 尝试直接运行并捕获错误
print("测试导入web_ui...")
stdin, stdout, stderr = ssh.exec_command(
    'cd /d D:\\VideoTranscode\\service && python -c "from web_ui import app; print(app)"'
)
out = stdout.read().decode()
err = stderr.read().decode()
print("输出:", out)
print("错误:", err)

# 查看日志
print("\n服务日志:")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\service\\service.log 2>nul')
log = stdout.read().decode()
print(log[-2000:] if len(log) > 2000 else log or "无日志")

ssh.close()
