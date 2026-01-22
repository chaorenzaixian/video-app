"""检查HTML更新"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 检查是否有长视频和短视频分开的上传入口
stdin, stdout, stderr = ssh.exec_command('findstr "longFileInput" D:\\VideoTranscode\\service\\templates\\index.html')
long = stdout.read().decode().strip()
print("长视频上传入口:", "已添加" if long else "未添加")

stdin, stdout, stderr = ssh.exec_command('findstr "shortFileInput" D:\\VideoTranscode\\service\\templates\\index.html')
short = stdout.read().decode().strip()
print("短视频上传入口:", "已添加" if short else "未添加")

stdin, stdout, stderr = ssh.exec_command('findstr "longLocalPath" D:\\VideoTranscode\\service\\templates\\index.html')
longLocal = stdout.read().decode().strip()
print("长视频本地路径:", "已添加" if longLocal else "未添加")

stdin, stdout, stderr = ssh.exec_command('findstr "shortLocalPath" D:\\VideoTranscode\\service\\templates\\index.html')
shortLocal = stdout.read().decode().strip()
print("短视频本地路径:", "已添加" if shortLocal else "未添加")

ssh.close()
