"""检查硬链接代码是否已上传"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查是否有os.link
print("检查os.link...")
stdin, stdout, stderr = ssh.exec_command('findstr "os.link" D:\\VideoTranscode\\service\\web_ui.py')
out = stdout.read().decode('utf-8', errors='ignore')
print(out if out else "未找到os.link")

# 检查Hard link
print("\n检查Hard link...")
stdin, stdout, stderr = ssh.exec_command('findstr "Hard link" D:\\VideoTranscode\\service\\web_ui.py')
out = stdout.read().decode('utf-8', errors='ignore')
print(out if out else "未找到Hard link")

# 测试API
print("\n测试API...")
import urllib.request
try:
    req = urllib.request.Request("http://198.176.60.121:8080/api/system")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(resp.read().decode())
except Exception as e:
    print(f"API错误: {e}")

ssh.close()
