"""检查上传错误"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查服务日志
print("检查最近的请求日志...")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\service\\service.log 2>nul')
log = stdout.read().decode('utf-8', errors='ignore')
if log:
    print(log[-2000:])
else:
    print("无日志文件")

# 检查uploads目录
print("\n检查uploads目录...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\uploads')
print(stdout.read().decode('gbk', errors='ignore'))

# 检查processing目录
print("\n检查processing目录...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
