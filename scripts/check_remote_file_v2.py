"""检查远程文件是否完整"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查文件大小
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\service\\templates\\index.html')
print('文件信息:')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查addLocalFile函数是否存在
stdin, stdout, stderr = ssh.exec_command('findstr /n "addLocalFile" D:\\VideoTranscode\\service\\templates\\index.html')
print('\naddLocalFile相关行:')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查文件末尾
stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\service\\templates\\index.html -Tail 15"')
print('\n文件末尾:')
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查服务是否正常运行（只看LISTENING）
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
print('\n端口监听状态:')
result = stdout.read().decode('gbk', errors='ignore')
print(result if result else '未监听')

ssh.close()
print('\n完成!')
