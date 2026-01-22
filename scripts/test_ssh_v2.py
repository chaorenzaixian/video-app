"""详细测试SSH连接 v2"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 详细测试SSH连接 ===')

# 直接执行Python代码
cmd = '''python -c "
import paramiko
import traceback
print('开始测试SSH连接...')
try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print('正在连接到 38.47.218.137...')
    client.connect('38.47.218.137', username='root', key_filename=r'C:\\server_key', timeout=30)
    print('连接成功!')
    stdin, stdout, stderr = client.exec_command('echo OK && hostname')
    print('输出:', stdout.read().decode())
    client.close()
except Exception as e:
    print('失败:', e)
    traceback.print_exc()
"'''

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')
print('stdout:', output)
if error:
    print('stderr:', error)

ssh.close()
