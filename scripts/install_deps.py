"""在转码服务器上安装依赖"""
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

print("安装 pillow 和 numpy...")
stdin, stdout, stderr = ssh.exec_command(
    "cd D:\\VideoTranscode\\service && pip install pillow numpy",
    timeout=120
)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
print("完成!")
