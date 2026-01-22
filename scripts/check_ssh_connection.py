"""检查转码服务器到主服务器的SSH连接"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 检查SSH密钥文件 ===')
stdin, stdout, stderr = ssh.exec_command('dir C:\\server_key')
output = stdout.read().decode('gbk', errors='ignore')
error = stderr.read().decode('gbk', errors='ignore')
print(output if output else error)

print('\n=== 测试SSH连接到主服务器 ===')
# 使用Python测试SSH连接
test_code = '''
import paramiko
import sys
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('38.47.218.137', username='root', key_filename='C:\\\\server_key', timeout=10)
    stdin, stdout, stderr = client.exec_command('echo "SSH OK"')
    print(stdout.read().decode())
    client.close()
    print("SSH连接成功!")
except Exception as e:
    print(f"SSH连接失败: {e}")
'''
stdin, stdout, stderr = ssh.exec_command(f'python -c "{test_code}"')
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print(output)
if error:
    print(f'错误: {error}')

print('\n=== 检查服务日志 ===')
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\logs\\service.log 2>nul | findstr /i "error\\|fail\\|ssh" | tail -20')
output = stdout.read().decode('utf-8', errors='ignore')
print(output if output else '无相关日志')

ssh.close()
