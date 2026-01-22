"""检查远程HTML文件特定行"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查第1270-1285行
cmd = 'powershell "Get-Content D:\\VideoTranscode\\service\\templates\\index.html | Select-Object -Skip 1269 -First 16"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print("第1270-1285行:")
print(out)

ssh.close()
