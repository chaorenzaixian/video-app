"""
重启转码服务
用法: python scripts/restart_transcode_service.py
"""
import paramiko
import time

def main():
    print("连接转码服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print("停止服务...")
    client.exec_command('taskkill /f /im python.exe 2>nul')
    time.sleep(3)
    
    print("启动服务...")
    cmd = 'wmic process call create "cmd /c cd /d D:\\VideoTranscode\\service && python web_ui.py"'
    client.exec_command(cmd)
    time.sleep(5)
    
    # 检查
    for i in range(5):
        stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
        result = stdout.read().decode('gbk', errors='ignore')
        if 'LISTENING' in result:
            print("✓ 服务已启动")
            print("访问地址: http://198.176.60.121:8080")
            client.close()
            return
        print(f"  等待启动... ({i+1}/5)")
        time.sleep(2)
    
    print("✗ 启动失败")
    client.close()

if __name__ == '__main__':
    main()
