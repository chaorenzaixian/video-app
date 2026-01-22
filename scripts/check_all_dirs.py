#!/usr/bin/env python3
"""检查所有目录"""
import paramiko

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    dirs = [
        "D:\\VideoTranscode\\downloads\\long",
        "D:\\VideoTranscode\\downloads\\short", 
        "D:\\VideoTranscode\\processing",
        "D:\\VideoTranscode\\completed\\long",
        "D:\\VideoTranscode\\completed\\short",
    ]
    
    for d in dirs:
        print(f"\n=== {d} ===")
        stdin, stdout, stderr = ssh.exec_command(f'dir /B "{d}" 2>nul')
        output = stdout.read().decode('utf-8', errors='replace').strip()
        print(output if output else "(空)")
    
    ssh.close()

if __name__ == "__main__":
    check()
