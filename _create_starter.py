# 在转码服务器桌面创建启动脚本
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print(f"连接转码服务器 {HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    
    print("连接成功！\n")
    
    # 创建启动脚本
    bat_content = '''@echo off
chcp 65001
echo ==========================================
echo   启动视频处理监控服务
echo ==========================================
echo.
cd /d D:\\VideoTranscode\\scripts
powershell -ExecutionPolicy Bypass -File watcher.ps1
pause
'''
    
    # 写入桌面
    sftp = ssh.open_sftp()
    desktop_path = "C:/Users/Administrator/Desktop/启动Watcher.bat"
    
    with sftp.open(desktop_path, 'w') as f:
        f.write(bat_content)
    
    print(f"已创建: {desktop_path}")
    
    # 同时创建一个后台运行版本
    bat_bg = '''@echo off
chcp 65001
echo 正在后台启动 Watcher...
start /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File D:\\VideoTranscode\\scripts\\watcher.ps1
echo 已启动！
timeout /t 3
'''
    
    desktop_path2 = "C:/Users/Administrator/Desktop/后台启动Watcher.bat"
    with sftp.open(desktop_path2, 'w') as f:
        f.write(bat_bg)
    
    print(f"已创建: {desktop_path2}")
    
    sftp.close()
    ssh.close()
    print("\n完成！请通过远程桌面双击运行")

if __name__ == "__main__":
    main()
