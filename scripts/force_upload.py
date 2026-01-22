"""强制上传web_ui.py"""
import paramiko
import time

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

sftp = ssh.open_sftp()

# 读取本地文件
local_file = 'transcode_service/web_ui.py'
with open(local_file, 'rb') as f:
    content = f.read()

print(f"本地文件大小: {len(content)} 字节")

# 检查是否有os.link
if b'os.link' in content:
    print("✓ 本地文件包含os.link")
else:
    print("✗ 本地文件不包含os.link")

# 上传
remote_file = 'D:/VideoTranscode/service/web_ui.py'
print(f"上传到 {remote_file}...")
sftp.put(local_file, remote_file)

# 验证
with sftp.file(remote_file, 'rb') as f:
    remote_content = f.read()

print(f"远程文件大小: {len(remote_content)} 字节")

if b'os.link' in remote_content:
    print("✓ 远程文件包含os.link")
else:
    print("✗ 远程文件不包含os.link")

sftp.close()

# 重启服务
print("\n重启服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(3)

# 启动服务
cmd = 'wmic process call create "cmd /c cd /d D:\\VideoTranscode\\service && python web_ui.py"'
ssh.exec_command(cmd)
time.sleep(5)

# 检查
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')

if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务启动失败")

ssh.close()
print("完成!")
