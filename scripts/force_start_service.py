"""
强制启动转码服务
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建启动批处理
    bat = '@echo off\r\ncd /d D:\\VideoTranscode\\service\r\npython service.py\r\n'
    with sftp.file('D:/VideoTranscode/run.bat', 'w') as f:
        f.write(bat)
    
    # 创建VBS隐藏启动
    vbs = 'Set ws = CreateObject("WScript.Shell")\r\nws.Run "D:\\VideoTranscode\\run.bat", 0, False\r\n'
    with sftp.file('D:/VideoTranscode/run.vbs', 'w') as f:
        f.write(vbs)
    
    sftp.close()
    
    print('启动服务...')
    stdin, stdout, stderr = client.exec_command('cscript //nologo D:\\VideoTranscode\\run.vbs')
    time.sleep(8)
    
    print('检查端口...')
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080"')
    result = stdout.read().decode('gbk', errors='ignore')
    print(result)
    
    if 'LISTENING' in result:
        print('\n✓ 服务启动成功！')
        
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/system')
        print('系统信息:', stdout.read().decode('utf-8', errors='ignore'))
    else:
        print('\n检查Python进程...')
        stdin, stdout, stderr = client.exec_command('tasklist | findstr python')
        procs = stdout.read().decode('gbk', errors='ignore')
        print(procs if procs else '无Python进程')
        
        # 尝试直接运行看错误
        print('\n尝试直接运行...')
        stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service & python service.py 2>&1', timeout=15)
        time.sleep(10)
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(4096).decode('gbk', errors='ignore'))
    
    client.close()

if __name__ == '__main__':
    main()
