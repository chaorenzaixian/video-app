"""
启动服务并检查
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 停止
    print("停止服务...")
    client.exec_command('taskkill /f /im python.exe 2>nul')
    client.exec_command('taskkill /f /im pythonw.exe 2>nul')
    time.sleep(3)
    
    # 启动
    print("启动服务...")
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python web_ui.py')
    time.sleep(6)
    
    # 检查端口
    stdin2, stdout2, stderr2 = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
    port = stdout2.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in port:
        print("OK: Service started")
        
        # 检查pending
        stdin3, stdout3, stderr3 = client.exec_command('curl -s http://localhost:8080/api/pending')
        pending = stdout3.read().decode('utf-8', errors='ignore')
        print(f"Pending: {pending[:500]}")
    else:
        print("FAIL: Service not started")
    
    client.close()

if __name__ == '__main__':
    main()
