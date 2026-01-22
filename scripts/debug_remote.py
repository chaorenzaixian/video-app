"""调试远程服务器"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查目录
print("检查目录...")
stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\service\\*.py')
out = stdout.read().decode('gbk', errors='ignore')
err = stderr.read().decode('gbk', errors='ignore')
print(out)
if err:
    print(f"错误: {err}")

# 检查web_ui.py
print("\n检查web_ui.py大小...")
stdin, stdout, stderr = ssh.exec_command('for %f in (D:\\VideoTranscode\\service\\web_ui.py) do @echo %~zf')
out = stdout.read().decode('gbk', errors='ignore')
print(f"文件大小: {out}")

# 尝试直接运行
print("\n尝试直接运行...")
stdin, stdout, stderr = ssh.exec_command('D: && cd D:\\VideoTranscode\\service && python -c "print(123)"')
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"输出: {out}")
if err:
    print(f"错误: {err}")

ssh.close()
