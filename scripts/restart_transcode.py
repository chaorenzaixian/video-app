"""
重启转码服务并检查状态
"""
import paramiko
import time

def main():
    print("连接转码服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 1. 停止现有进程
    print("停止现有Python进程...")
    client.exec_command('taskkill /f /im python.exe 2>nul')
    client.exec_command('taskkill /f /im pythonw.exe 2>nul')
    time.sleep(3)
    
    # 2. 创建启动脚本
    print("创建启动脚本...")
    sftp = client.open_sftp()
    
    # 创建一个简单的启动bat
    start_bat = '''@echo off
cd /d D:\\VideoTranscode\\service
start "" /b pythonw web_ui.py
'''
    with sftp.file('D:/VideoTranscode/start_web.bat', 'w') as f:
        f.write(start_bat)
    
    sftp.close()
    
    # 3. 执行启动脚本
    print("启动服务...")
    client.exec_command('D:\\VideoTranscode\\start_web.bat')
    time.sleep(5)
    
    # 4. 检查端口
    print("检查服务状态...")
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
    result = stdout.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in result:
        print("✓ 服务已启动，端口8080正在监听")
        
        # 检查API
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/system')
        api_result = stdout.read().decode('utf-8', errors='ignore')
        print(f"API响应: {api_result}")
        
        # 检查pending
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
        pending_result = stdout.read().decode('utf-8', errors='ignore')
        print(f"Pending任务: {pending_result[:200]}...")
    else:
        print("✗ 服务启动失败")
        
        # 尝试查看错误
        print("\n尝试查看启动错误...")
        stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python -c "import web_ui" 2>&1')
        time.sleep(3)
        result = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        if result:
            print(f"输出: {result}")
        if err:
            print(f"错误: {err}")
    
    client.close()
    print("\n完成!")

if __name__ == '__main__':
    main()
