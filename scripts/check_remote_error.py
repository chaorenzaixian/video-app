"""检查远程服务器上的错误"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查文件是否存在
print("检查文件...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\service\\web_ui.py', timeout=10)
out = stdout.read().decode('gbk', errors='ignore')
print(out)

# 尝试直接运行Python检查语法
print("检查web_ui.py语法...")
stdin, stdout, stderr = ssh.exec_command('D: & cd D:\\VideoTranscode\\service & python -m py_compile web_ui.py', timeout=30)
err = stderr.read().decode('gbk', errors='ignore')
if err:
    print("语法错误:", err)
else:
    print("语法正确")

# 尝试启动服务并捕获错误
print("\n尝试启动服务...")
stdin, stdout, stderr = ssh.exec_command('D: & cd D:\\VideoTranscode\\service & python web_ui.py', timeout=15)
try:
    out = stdout.read().decode('gbk', errors='ignore')
    err = stderr.read().decode('gbk', errors='ignore')
    print("输出:", out[:500] if out else "无输出")
    print("错误:", err[:500] if err else "无错误")
except:
    pass

ssh.close()
