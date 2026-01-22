"""
检查转码服务Flask输出
"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username=user, password=password, timeout=30)

# 检查nohup输出
commands = [
    'type D:\\VideoTranscode\\service\\nohup.out 2>nul',
    'type D:\\VideoTranscode\\logs\\web_ui.log 2>nul',
    'dir D:\\VideoTranscode\\logs\\',
]

for cmd in commands:
    print(f"\n=== {cmd} ===")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
    output = stdout.read().decode('gbk', errors='ignore')
    if output.strip():
        lines = output.strip().split('\n')
        for line in lines[-30:]:
            print(line)
    else:
        err = stderr.read().decode('gbk', errors='ignore')
        if err:
            print(f"Error: {err}")
        else:
            print("(empty)")

client.close()
