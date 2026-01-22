"""检查远程服务器上的browse API"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

stdin, stdout, stderr = ssh.exec_command('findstr "browse" D:\\VideoTranscode\\service\\web_ui.py', timeout=30)
result = stdout.read().decode('gbk', errors='ignore')
print('browse搜索结果:', result if result else '未找到')

ssh.close()
