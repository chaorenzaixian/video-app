"""
重启服务
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
    
    # 检查是否停止
    stdin, stdout, stderr = client.exec_command('tasklist | findstr python')
    result = stdout.read().decode('gbk', errors='ignore')
    print(f"Python进程: {result.strip() if result.strip() else '无'}")
    
    # 启动
    print("启动服务...")
    client.exec_command('cd /d D:\\VideoTranscode\\service && start "" python web_ui.py')
    time.sleep(8)
    
    # 检查端口
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
    port = stdout.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in port:
        print("OK: 服务已启动")
        
        # 检查pending
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
        pending = stdout.read().decode('utf-8', errors='ignore')
        
        import json
        data = json.loads(pending) if pending else {}
        items = data.get('items', [])
        print(f"Pending任务数: {len(items)}")
        for item in items[:3]:
            print(f"  - {item.get('task_id')}: {item.get('filename', 'unknown')}")
    else:
        print("FAIL: 服务未启动")
        
        # 检查错误
        stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python -c "import web_ui"')
        time.sleep(3)
        err = stderr.read().decode('utf-8', errors='ignore')
        if err:
            print(f"错误: {err}")
    
    client.close()

if __name__ == '__main__':
    main()
