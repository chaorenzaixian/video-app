"""重启转码服务"""
import paramiko
import time

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 先杀掉所有python进程
print("停止现有服务...")
ssh.exec_command('taskkill /f /im python.exe 2>nul')
time.sleep(3)

# 启动服务
print("启动服务...")
cmd = 'wmic process call create "cmd /c D: & cd D:\\VideoTranscode\\service & python web_ui.py"'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('启动命令结果:', stdout.read().decode('gbk', errors='ignore'))
time.sleep(10)

# 检查端口
stdin, stdout, stderr = ssh.exec_command('netstat -an | findstr "8080" | findstr "LISTENING"')
result = stdout.read().decode('gbk', errors='ignore')
if 'LISTENING' in result:
    print('✓ 服务已启动')
else:
    print('✗ 服务未监听')
    # 检查错误日志
    stdin, stdout, stderr = ssh.exec_command('type D:\\VideoTranscode\\service\\error.log 2>nul')
    err = stdout.read().decode('gbk', errors='ignore')
    if err:
        print('错误日志:', err[-500:])

ssh.close()
print("完成!")
