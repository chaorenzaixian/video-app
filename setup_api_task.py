#!/usr/bin/env python3
"""使用Windows计划任务启动API"""
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

# 1. 删除旧的计划任务
print("\n1. 删除旧计划任务...")
ssh.exec_command('schtasks /delete /tn "TranscodeStatusAPI" /f')
time.sleep(1)

# 2. 创建新的计划任务
print("\n2. 创建计划任务...")
# 使用schtasks创建一个立即运行的任务
create_cmd = 'schtasks /create /tn "TranscodeStatusAPI" /tr "C:\\Python314\\python.exe D:\\VideoTranscode\\status_api.py" /sc onstart /ru SYSTEM /rl HIGHEST /f'
stdin, stdout, stderr = ssh.exec_command(create_cmd)
out = stdout.read().decode('gbk', errors='ignore')
err = stderr.read().decode('gbk', errors='ignore')
print(f"输出: {out}")
if err:
    print(f"错误: {err}")

# 3. 立即运行任务
print("\n3. 运行计划任务...")
stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "TranscodeStatusAPI"')
out = stdout.read().decode('gbk', errors='ignore')
print(f"输出: {out}")
time.sleep(5)

# 4. 检查任务状态
print("\n4. 检查任务状态...")
stdin, stdout, stderr = ssh.exec_command('schtasks /query /tn "TranscodeStatusAPI" /fo list')
print(stdout.read().decode('gbk', errors='ignore'))

# 5. 检查进程
print("\n5. 检查Python进程:")
stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
print(stdout.read().decode('gbk', errors='ignore'))

# 6. 检查端口
print("\n6. 检查端口5001:")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port = stdout.read().decode('gbk', errors='ignore')
print(port if port else "端口5001未监听")

# 7. 测试API
print("\n7. 测试API:")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
response = stdout.read().decode()
print(f"响应: {response}")

# 如果还是不行，尝试用pythonw
if 'ok' not in response:
    print("\n8. 尝试使用pythonw...")
    # 先检查pythonw是否存在
    stdin, stdout, stderr = ssh.exec_command('where pythonw')
    pythonw_path = stdout.read().decode().strip()
    print(f"pythonw路径: {pythonw_path}")
    
    if pythonw_path:
        # 删除旧任务
        ssh.exec_command('schtasks /delete /tn "TranscodeStatusAPI" /f')
        time.sleep(1)
        
        # 用pythonw创建任务
        create_cmd = f'schtasks /create /tn "TranscodeStatusAPI" /tr "{pythonw_path} D:\\VideoTranscode\\status_api.py" /sc onstart /ru SYSTEM /rl HIGHEST /f'
        stdin, stdout, stderr = ssh.exec_command(create_cmd)
        print(stdout.read().decode('gbk', errors='ignore'))
        
        # 运行
        stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "TranscodeStatusAPI"')
        time.sleep(5)
        
        # 检查
        stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
        port = stdout.read().decode('gbk', errors='ignore')
        print(f"端口: {port}" if port else "端口5001仍未监听")

ssh.close()
print("\n完成")
