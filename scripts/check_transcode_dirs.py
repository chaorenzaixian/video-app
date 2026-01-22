"""检查转码服务器目录"""
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

cmds = [
    'dir D:\\VideoTranscode /b',
    'dir D:\\VideoTranscode\\input /b 2>nul || echo (空)',
    'dir D:\\VideoTranscode\\output /b 2>nul || echo (空)',
]

for cmd in cmds:
    print(f"\n> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
