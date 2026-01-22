"""
调试转码服务
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 测试导入
    print('测试导入...')
    cmd = 'cd /d D:\\VideoTranscode\\service && python -c "from web_ui import app; print(app)"'
    stdin, stdout, stderr = client.exec_command(cmd)
    time.sleep(5)
    result = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print('输出:', result)
    print('错误:', err)
    
    # 如果有错误，检查具体问题
    if err:
        print('\n检查config...')
        cmd = 'cd /d D:\\VideoTranscode\\service && python -c "from config import *; print(DIRS)"'
        stdin, stdout, stderr = client.exec_command(cmd)
        time.sleep(3)
        result = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        print('Config输出:', result)
        print('Config错误:', err)
    
    client.close()

if __name__ == '__main__':
    main()
