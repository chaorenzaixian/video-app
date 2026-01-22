"""修复远程web_ui.py文件"""
import paramiko

# 读取本地正确的文件
with open('transcode_service/web_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"本地文件大小: {len(content)} 字节")

# 连接远程服务器
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 上传文件
sftp = ssh.open_sftp()
sftp.put('transcode_service/web_ui.py', 'D:/VideoTranscode/service/web_ui.py')
sftp.close()
print("文件已上传")

# 检查语法
stdin, stdout, stderr = ssh.exec_command('D: & cd D:\\VideoTranscode\\service & python -m py_compile web_ui.py', timeout=30)
err = stderr.read().decode('gbk', errors='ignore')
if err:
    print("语法错误:", err)
else:
    print("语法正确")

# 重启服务
print("重启服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
import time
time.sleep(2)

cmd = 'wmic process call create "cmd /c D: & cd D:\\VideoTranscode\\service & python web_ui.py"'
ssh.exec_command(cmd)
time.sleep(8)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务未监听")

ssh.close()
