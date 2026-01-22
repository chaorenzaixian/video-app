#!/usr/bin/env python3
"""测试watcher脚本"""
import paramiko
import time

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def test():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 测试运行脚本
    print("测试运行watcher脚本...")
    cmd = 'powershell -ExecutionPolicy Bypass -Command "& {Set-Location D:\\VideoTranscode\\scripts; .\\watcher.ps1}" 2>&1'
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    
    try:
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        print(f"输出:\n{output[:2000]}")
        if error:
            print(f"错误:\n{error[:1000]}")
    except Exception as e:
        print(f"读取超时（正常，脚本在运行）: {e}")
    
    ssh.close()

if __name__ == "__main__":
    test()
