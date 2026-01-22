"""检查远程服务器上的get_queue函数"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查get_queue函数
print("检查远程服务器上的get_queue函数:")
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py | Select-String -Pattern \"def get_queue|status not in|status in\" -Context 0,3"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查pending_publish的内容
print("\n检查pending_publish中的任务状态:")
cmd = r'powershell -Command "Invoke-WebRequest -Uri http://localhost:8080/api/system -UseBasicParsing | Select-Object -ExpandProperty Content"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
