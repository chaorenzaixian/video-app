"""
检查guardian日志
"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

# 检查guardian日志最后100行
cmd = 'powershell "Get-Content D:\\VideoTranscode\\logs\\guardian.log -Tail 100"'
print(f"=== Guardian Log ===")
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

client.close()
