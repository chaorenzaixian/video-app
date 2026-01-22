#!/usr/bin/env python3
"""在转码服务器桌面创建启动脚本"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

# 启动脚本内容
STARTER_SCRIPT = '''@echo off
title Video Watcher Service
cd /d D:\\VideoTranscode\\scripts
powershell -ExecutionPolicy Bypass -NoExit -File watcher.ps1
pause
'''

def create():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 创建桌面启动脚本
    sftp = ssh.open_sftp()
    
    desktop_path = "C:/Users/Administrator/Desktop/Start_Watcher.bat"
    print(f"创建桌面启动脚本: {desktop_path}")
    
    with sftp.file(desktop_path, 'w') as f:
        f.write(STARTER_SCRIPT)
    
    sftp.close()
    
    print("启动脚本创建完成!")
    print("\n在远程桌面双击 'Start_Watcher.bat' 即可启动转码服务")
    
    ssh.close()

if __name__ == "__main__":
    create()
