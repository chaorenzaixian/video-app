"""
在转码服务器上测试paramiko连接
"""
import paramiko

# 转码服务器
TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

print("1. 连接转码服务器...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("   连接成功")

# 创建测试脚本
test_script = '''
import paramiko
import traceback

try:
    print("开始连接...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("尝试连接 38.47.218.137...")
    client.connect("38.47.218.137", username="root", key_filename="C:\\\\server_key", timeout=30)
    print("连接成功，执行命令...")
    stdin, stdout, stderr = client.exec_command("echo OK", timeout=10)
    result = stdout.read().decode()
    print(f"命令结果: {result}")
    client.close()
    print("完成")
except Exception as e:
    print(f"错误: {e}")
    traceback.print_exc()
'''

# 写入测试脚本
sftp = client.open_sftp()
with sftp.file('D:/test_paramiko.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("\n2. 运行测试脚本...")
stdin, stdout, stderr = client.exec_command('python D:/test_paramiko.py', timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"stdout:\n{out}")
if err:
    print(f"stderr:\n{err}")

client.close()
