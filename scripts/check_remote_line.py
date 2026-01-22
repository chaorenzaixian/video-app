"""检查远程文件第250行附近"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 读取第245-260行
print("读取第245-260行...")
stdin, stdout, stderr = ssh.exec_command('powershell "Get-Content D:\\VideoTranscode\\service\\web_ui.py | Select-Object -Skip 244 -First 16"', timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(out)

ssh.close()
