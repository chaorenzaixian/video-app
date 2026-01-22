"""
调试启动问题
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 测试导入
    print("测试导入...")
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python -c "import web_ui; print(web_ui.app)"')
    time.sleep(5)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(f"输出: {out}")
    print(f"错误: {err}")
    
    if not err:
        # 直接运行
        print("\n直接运行web_ui...")
        stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python web_ui.py')
        time.sleep(8)
        
        # 检查端口
        stdin2, stdout2, stderr2 = client.exec_command('netstat -an | findstr ":8080"')
        port = stdout2.read().decode('gbk', errors='ignore')
        print(f"端口状态: {port}")
        
        if 'LISTENING' in port:
            stdin3, stdout3, stderr3 = client.exec_command('curl -s http://localhost:8080/api/pending')
            pending = stdout3.read().decode('utf-8', errors='ignore')
            print(f"Pending: {pending[:300]}")
    
    client.close()

if __name__ == '__main__':
    main()
