"""
测试从转码服务器上传到主服务器的速度
"""
import paramiko
import time

# 转码服务器
TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)

# 测试上传一个小文件
test_script = '''
import paramiko
import os
import time

# 创建测试文件 (10MB)
test_file = "D:/test_upload.bin"
with open(test_file, "wb") as f:
    f.write(os.urandom(10 * 1024 * 1024))

print(f"测试文件大小: 10 MB")

# 连接主服务器
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("38.47.218.137", username="root", key_filename="C:\\\\server_key", timeout=30)
sftp = client.open_sftp()

# 上传
start = time.time()
sftp.put(test_file, "/tmp/test_upload.bin")
elapsed = time.time() - start

print(f"上传耗时: {elapsed:.2f} 秒")
print(f"上传速度: {10 / elapsed:.2f} MB/s")

# 清理
sftp.remove("/tmp/test_upload.bin")
sftp.close()
client.close()
os.remove(test_file)
print("完成")
'''

# 写入并运行测试脚本
sftp = client.open_sftp()
with sftp.file('D:/test_upload_speed.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("测试上传速度...")
stdin, stdout, stderr = client.exec_command('python D:/test_upload_speed.py', timeout=300)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(out)
if err:
    print(f"错误: {err}")

client.close()
