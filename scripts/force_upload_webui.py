"""强制上传web_ui.py并验证"""
import paramiko
import time

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

sftp = ssh.open_sftp()

# 读取本地文件
print("读取本地文件...")
with open('transcode_service/web_ui.py', 'rb') as f:
    local_content = f.read()
print(f"本地文件大小: {len(local_content)} bytes")

# 检查本地文件中的get_queue函数
local_str = local_content.decode('utf-8')
if 'def get_queue():' in local_str:
    # 找到get_queue函数的内容
    start = local_str.find('def get_queue():')
    end = local_str.find('def get_pending():', start)
    print(f"\n本地get_queue函数:\n{local_str[start:end][:500]}")

# 上传文件
print("\n上传文件...")
remote_path = 'D:/VideoTranscode/service/web_ui.py'
with sftp.file(remote_path, 'wb') as f:
    f.write(local_content)
print("上传完成")

# 验证上传
print("\n验证上传...")
with sftp.file(remote_path, 'rb') as f:
    remote_content = f.read()
print(f"远程文件大小: {len(remote_content)} bytes")

if local_content == remote_content:
    print("✓ 文件内容一致")
else:
    print("✗ 文件内容不一致!")
    # 找出差异
    for i, (a, b) in enumerate(zip(local_content, remote_content)):
        if a != b:
            print(f"  第一个差异在位置 {i}: 本地={a}, 远程={b}")
            break

sftp.close()

# 重启服务
print("\n重启服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(3)

cmd = 'wmic process call create "cmd /c D: & cd D:\\VideoTranscode\\service & python web_ui.py"'
ssh.exec_command(cmd)
time.sleep(10)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
if 'LISTENING' in result:
    print("✓ 服务已启动")
else:
    print("✗ 服务启动失败")

# 再次验证代码
print("\n验证远程代码...")
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py | Select-String -Pattern \"def get_queue\" -Context 0,5"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))

ssh.close()
print("\n完成!")
