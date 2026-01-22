"""
检查转码服务器的日志
"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

# 检查服务日志
stdin, stdout, stderr = client.exec_command('type D:\\VideoTranscode\\logs\\service.log | more +1', timeout=30)
print("=== 服务日志 (最后部分) ===")
output = stdout.read().decode('gbk', errors='ignore')
lines = output.strip().split('\n')
for line in lines[-50:]:
    print(line)

client.close()
