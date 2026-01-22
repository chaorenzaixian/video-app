"""
测试从转码服务器到主服务器的SSH上传
"""
import paramiko
import time

# 转码服务器
TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

# 主服务器
MAIN_HOST = "38.47.218.137"
MAIN_KEY = "C:\\server_key"

print("1. 连接转码服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("   连接成功")

# 测试从转码服务器SSH到主服务器
print("\n2. 测试转码服务器到主服务器的SSH连接...")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@{MAIN_HOST} "echo OK"'
print(f"   命令: {cmd}")
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"   stdout: {out}")
print(f"   stderr: {err}")

# 检查SSH密钥是否存在
print("\n3. 检查SSH密钥文件...")
cmd = f'dir {MAIN_KEY}'
stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
out = stdout.read().decode('gbk', errors='ignore')
print(out)

# 测试Python paramiko连接
print("\n4. 测试Python脚本中的SSH连接...")
test_script = '''
import paramiko
import sys

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("38.47.218.137", username="root", key_filename="C:\\\\server_key", timeout=30)
    stdin, stdout, stderr = client.exec_command("echo OK", timeout=10)
    print("SSH连接成功:", stdout.read().decode())
    client.close()
except Exception as e:
    print("SSH连接失败:", str(e))
'''

cmd = f'python -c "{test_script}"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"   stdout: {out}")
if err:
    print(f"   stderr: {err}")

client.close()
print("\n完成")
