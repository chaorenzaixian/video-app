"""检查服务启动问题"""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查web_ui.py语法
print("检查web_ui.py语法...")
stdin, stdout, stderr = ssh.exec_command('cd D:\\VideoTranscode\\service && python -m py_compile web_ui.py')
err = stderr.read().decode()
if err:
    print(f"语法错误: {err}")
else:
    print("语法检查通过")

# 尝试导入
print("\n尝试导入web_ui...")
stdin, stdout, stderr = ssh.exec_command('cd D:\\VideoTranscode\\service && python -c "import web_ui"')
out = stdout.read().decode()
err = stderr.read().decode()
if out:
    print(f"输出: {out}")
if err:
    print(f"错误: {err}")

# 检查文件内容
print("\n检查add_local_file函数...")
stdin, stdout, stderr = ssh.exec_command('cd D:\\VideoTranscode\\service && findstr /n "os.link" web_ui.py')
out = stdout.read().decode()
print(out if out else "未找到os.link")

ssh.close()
