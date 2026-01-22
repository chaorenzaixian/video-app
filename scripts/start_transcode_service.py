"""
在转码服务器上启动转码服务（后台运行）
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print("=== 检查是否已有服务在运行 ===")
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    if 'LISTENING' in result:
        print("服务已在运行！")
        print(result)
        
        # 测试访问
        print("\n=== 测试Web界面 ===")
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/categories')
        print(stdout.read().decode('utf-8', errors='ignore'))
        
        client.close()
        return
    
    print("服务未运行，正在启动...")
    
    # 创建启动脚本
    start_script = '''
@echo off
cd /d D:\\VideoTranscode\\service
start /b python service.py > D:\\VideoTranscode\\logs\\service_output.log 2>&1
echo Service started
'''
    
    # 写入启动脚本
    sftp = client.open_sftp()
    with sftp.file('D:/VideoTranscode/start_service.bat', 'w') as f:
        f.write(start_script)
    sftp.close()
    
    # 执行启动脚本
    stdin, stdout, stderr = client.exec_command('D:\\VideoTranscode\\start_service.bat')
    time.sleep(3)
    print(stdout.read().decode('gbk', errors='ignore'))
    
    # 检查是否启动成功
    print("\n=== 检查端口 ===")
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    print(result)
    
    if 'LISTENING' in result:
        print("\n✓ 服务启动成功！")
        print("Web管理界面: http://198.176.60.121:8080")
    else:
        print("\n✗ 服务启动失败，检查日志...")
        stdin, stdout, stderr = client.exec_command('type D:\\VideoTranscode\\logs\\service_output.log')
        print(stdout.read().decode('gbk', errors='ignore'))
    
    client.close()

if __name__ == '__main__':
    main()
