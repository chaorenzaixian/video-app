"""详细测试SSH连接"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 详细测试SSH连接 ===')

# 写一个测试脚本到远程
test_script = r'''
import paramiko
import traceback

print("开始测试SSH连接...")
print("目标: 38.47.218.137")
print("密钥: C:\\server_key")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("正在连接...")
    client.connect('38.47.218.137', username='root', key_filename=r'C:\server_key', timeout=30)
    print("连接成功!")
    
    stdin, stdout, stderr = client.exec_command('echo "Hello from main server" && hostname')
    out = stdout.read().decode()
    err = stderr.read().decode()
    print(f"输出: {out}")
    if err:
        print(f"错误: {err}")
    
    client.close()
    print("测试完成!")
except Exception as e:
    print(f"连接失败: {e}")
    traceback.print_exc()
'''

# 保存脚本到远程
stdin, stdout, stderr = ssh.exec_command(f'echo {repr(test_script)} > D:\\test_ssh.py')
stdout.read()

# 执行脚本
print("执行测试脚本...")
stdin, stdout, stderr = ssh.exec_command('cd D:\\ && python test_ssh.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(output)
if error:
    print(f'stderr: {error}')

ssh.close()
