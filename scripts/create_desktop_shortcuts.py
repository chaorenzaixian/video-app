"""
在转码服务器桌面创建快捷方式
"""
import paramiko

def main():
    print("连接转码服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建启动服务的bat文件
    start_bat = '''@echo off
cd /d D:\\VideoTranscode\\service
echo 启动转码服务...
python web_ui.py
pause
'''
    with sftp.file('D:/VideoTranscode/service/启动服务.bat', 'w') as f:
        f.write(start_bat)
    print("✓ 创建 启动服务.bat")
    
    # 创建重启服务的bat文件
    restart_bat = '''@echo off
echo 停止服务...
taskkill /f /im python.exe 2>nul
timeout /t 3 /nobreak >nul
echo 启动服务...
cd /d D:\\VideoTranscode\\service
start "" python web_ui.py
echo 服务已启动
timeout /t 3
'''
    with sftp.file('D:/VideoTranscode/service/重启服务.bat', 'w') as f:
        f.write(restart_bat)
    print("✓ 创建 重启服务.bat")
    
    # 创建打开管理页面的bat文件
    open_bat = '''@echo off
start http://localhost:8080
'''
    with sftp.file('D:/VideoTranscode/service/打开管理页面.bat', 'w') as f:
        f.write(open_bat)
    print("✓ 创建 打开管理页面.bat")
    
    sftp.close()
    
    # 复制到桌面
    print("\n复制到桌面...")
    client.exec_command('copy "D:\\VideoTranscode\\service\\启动服务.bat" "C:\\Users\\Administrator\\Desktop\\"')
    client.exec_command('copy "D:\\VideoTranscode\\service\\重启服务.bat" "C:\\Users\\Administrator\\Desktop\\"')
    client.exec_command('copy "D:\\VideoTranscode\\service\\打开管理页面.bat" "C:\\Users\\Administrator\\Desktop\\"')
    
    import time
    time.sleep(2)
    
    # 验证
    stdin, stdout, stderr = client.exec_command('dir "C:\\Users\\Administrator\\Desktop\\*.bat"')
    result = stdout.read().decode('gbk', errors='ignore')
    
    if '启动服务' in result:
        print("✓ 桌面快捷方式创建成功")
    else:
        print("✗ 创建失败")
    
    client.close()
    print("\n完成!")

if __name__ == '__main__':
    main()
