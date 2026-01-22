"""
修复并启动转码服务
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建正确的启动脚本
    bat_content = '''@echo off
cd /d D:\\VideoTranscode\\service
python service.py
'''
    
    with sftp.file('D:/VideoTranscode/start_service.bat', 'w') as f:
        f.write(bat_content)
    print("已更新 start_service.bat")
    
    # 创建PowerShell启动脚本
    ps_content = '''
$process = Start-Process -FilePath "python" -ArgumentList "service.py" -WorkingDirectory "D:\\VideoTranscode\\service" -WindowStyle Hidden -PassThru
Write-Host "Started process ID: $($process.Id)"
'''
    
    with sftp.file('D:/VideoTranscode/start_service.ps1', 'w') as f:
        f.write(ps_content)
    print("已创建 start_service.ps1")
    
    sftp.close()
    
    # 使用PowerShell启动
    print("\n启动服务...")
    stdin, stdout, stderr = client.exec_command('powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\start_service.ps1')
    print(stdout.read().decode('gbk', errors='ignore'))
    print(stderr.read().decode('gbk', errors='ignore'))
    
    time.sleep(5)
    
    # 检查端口
    print("\n检查端口...")
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    print(result)
    
    if 'LISTENING' in result:
        print("\n✓ 服务启动成功！")
        print("Web界面: http://198.176.60.121:8080")
        
        # 测试API
        print("\n测试API...")
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/categories | head -c 100')
        print(stdout.read().decode('utf-8', errors='ignore'))
    else:
        print("\n✗ 服务未启动")
        # 检查Python进程
        stdin, stdout, stderr = client.exec_command('tasklist | findstr python')
        print("Python进程:")
        print(stdout.read().decode('gbk', errors='ignore'))
    
    client.close()

if __name__ == '__main__':
    main()
