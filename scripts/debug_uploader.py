"""
在转码服务器上调试Uploader
"""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

# 创建调试脚本
debug_script = '''
import sys
sys.path.insert(0, "D:\\\\VideoTranscode\\\\service")

from uploader import Uploader
import os

print("测试Uploader...")
uploader = Uploader()

# 测试连接
print("1. 测试连接...")
if uploader._connect():
    print("   连接成功")
else:
    print("   连接失败!")
    sys.exit(1)

# 测试上传小文件
print("2. 测试上传小文件...")
test_file = "D:\\\\test_upload.txt"
with open(test_file, "w") as f:
    f.write("test content")

result = uploader.upload_file(test_file, "/tmp/test_upload.txt")
print(f"   上传结果: {result}")

# 清理
os.remove(test_file)
uploader._run_ssh("rm /tmp/test_upload.txt")

print("3. 检查当前连接状态...")
print(f"   _client: {uploader._client}")
print(f"   _sftp: {uploader._sftp}")

print("完成")
'''

sftp = client.open_sftp()
with sftp.file('D:/debug_uploader.py', 'w') as f:
    f.write(debug_script)
sftp.close()

print("运行调试脚本...")
stdin, stdout, stderr = client.exec_command('python D:/debug_uploader.py', timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(out)
if err:
    print(f"错误:\n{err}")

client.close()
