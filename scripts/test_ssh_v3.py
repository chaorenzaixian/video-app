"""详细测试SSH连接 v3 - 使用文件"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 创建测试脚本 ===')

# 创建测试脚本
script_content = '''import paramiko
import traceback
import sys

print("Python version:", sys.version)
print("Paramiko version:", paramiko.__version__)
print("")
print("Testing SSH connection to 38.47.218.137...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_path = r"C:\\server_key"
    print(f"Using key: {key_path}")
    
    import os
    if os.path.exists(key_path):
        print("Key file exists")
        with open(key_path, 'r') as f:
            first_line = f.readline().strip()
            print(f"Key type: {first_line}")
    else:
        print("Key file NOT found!")
        sys.exit(1)
    
    print("Connecting...")
    client.connect('38.47.218.137', username='root', key_filename=key_path, timeout=30)
    print("Connected!")
    
    stdin, stdout, stderr = client.exec_command('echo "SUCCESS" && hostname && date')
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"Output: {out}")
    if err:
        print(f"Stderr: {err}")
    
    client.close()
    print("Test completed successfully!")
    
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
'''

# 使用SFTP上传脚本
sftp = ssh.open_sftp()
with sftp.file('D:/test_ssh_conn.py', 'w') as f:
    f.write(script_content)
sftp.close()

print('脚本已上传，执行中...')

# 执行脚本
stdin, stdout, stderr = ssh.exec_command('python D:\\test_ssh_conn.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print('\n=== 执行结果 ===')
print(output)
if error:
    print('Stderr:', error)

ssh.close()
