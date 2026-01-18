#!/usr/bin/env python3
"""调试API启动问题"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("✓ 已连接")

# 1. 检查Python版本和路径
print("\n1. Python环境:")
stdin, stdout, stderr = ssh.exec_command('where python')
print(f"路径: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('python --version')
print(f"版本: {stdout.read().decode().strip()}")

# 2. 检查Flask是否可导入
print("\n2. 测试Flask导入:")
stdin, stdout, stderr = ssh.exec_command('python -c "from flask import Flask; print(\'Flask OK\')"')
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(f"输出: {out}")
if err:
    print(f"错误: {err}")

# 3. 检查status_api.py语法
print("\n3. 检查语法:")
stdin, stdout, stderr = ssh.exec_command('python -m py_compile D:\\VideoTranscode\\status_api.py')
err = stderr.read().decode().strip()
if err:
    print(f"语法错误: {err}")
else:
    print("语法正确")

# 4. 尝试直接运行（带超时）
print("\n4. 尝试启动API（5秒后检查）...")
# 使用PowerShell启动
ps_cmd = '''powershell -Command "Start-Process python -ArgumentList 'D:\\VideoTranscode\\status_api.py' -WorkingDirectory 'D:\\VideoTranscode' -RedirectStandardOutput 'D:\\VideoTranscode\\logs\\api_out.log' -RedirectStandardError 'D:\\VideoTranscode\\logs\\api_err.log'"'''
stdin, stdout, stderr = ssh.exec_command(ps_cmd)
time.sleep(5)

# 5. 检查进程和端口
print("\n5. 检查进程:")
stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
print(stdout.read().decode('gbk', errors='ignore'))

print("\n6. 检查端口:")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port = stdout.read().decode('gbk', errors='ignore')
print(port if port else "端口5001未监听")

# 7. 查看错误日志
print("\n7. 错误日志:")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\logs\\api_err.log 2>nul')
err_log = stdout.read().decode('gbk', errors='ignore')
print(err_log if err_log else "无错误日志")

print("\n8. 输出日志:")
stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\logs\\api_out.log 2>nul')
out_log = stdout.read().decode('gbk', errors='ignore')
print(out_log if out_log else "无输出日志")

# 8. 尝试用nohup方式启动
print("\n9. 尝试另一种启动方式...")
# 创建一个启动脚本
start_script = '''
cd /d D:\\VideoTranscode
start /min cmd /c "python status_api.py"
'''
sftp = ssh.open_sftp()
with sftp.file('D:\\VideoTranscode\\run_api.bat', 'w') as f:
    f.write(start_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('D:\\VideoTranscode\\run_api.bat')
time.sleep(3)

print("\n10. 再次检查:")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port = stdout.read().decode('gbk', errors='ignore')
print(f"端口: {port}" if port else "端口5001仍未监听")

stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
print(stdout.read().decode('gbk', errors='ignore'))

ssh.close()
