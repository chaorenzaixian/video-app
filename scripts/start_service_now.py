"""
立即启动转码服务
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print('直接启动服务...')
    # 使用nohup方式启动
    stdin, stdout, stderr = client.exec_command(
        'cd /d D:\\VideoTranscode\\service & start /b python service.py',
        timeout=10
    )
    time.sleep(8)
    
    print('检查端口...')
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr "0.0.0.0:8080"')
    result = stdout.read().decode('gbk', errors='ignore')
    print(result)
    
    if 'LISTENING' in result:
        print('\n✓ 服务启动成功！')
        print('Web界面: http://198.176.60.121:8080')
        
        # 测试API
        print('\n测试API...')
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/system')
        print(stdout.read().decode('utf-8', errors='ignore'))
    else:
        print('\n服务未启动，尝试查看进程...')
        stdin, stdout, stderr = client.exec_command('tasklist | findstr python')
        print(stdout.read().decode('gbk', errors='ignore'))
    
    client.close()

if __name__ == '__main__':
    main()
