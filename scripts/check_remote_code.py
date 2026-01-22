"""检查远程代码"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=== 检查远程web_ui.py中的get_history函数 ===')
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py | Select-String -Pattern \"def get_history|/api/history|get_publish_history\" -Context 0,5"'
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

print('\n=== 检查远程task_queue.py中的get_publish_history函数 ===')
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\task_queue.py | Select-String -Pattern \"def get_publish_history\" -Context 0,10"'
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

ssh.close()
