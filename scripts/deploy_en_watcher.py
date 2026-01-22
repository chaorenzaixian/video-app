#!/usr/bin/env python3
"""部署英文版watcher脚本到转码服务器"""
import paramiko
import os

TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

def deploy():
    # 读取英文版脚本
    script_path = os.path.join(os.path.dirname(__file__), "watcher_en.ps1")
    with open(script_path, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接转码服务器 {TRANSCODE_HOST}...")
    ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS)
    
    # 备份旧脚本
    print("备份旧脚本...")
    ssh.exec_command('powershell -Command "Copy-Item D:\\VideoTranscode\\scripts\\watcher.ps1 D:\\VideoTranscode\\scripts\\watcher_backup.ps1 -Force"')
    
    # 上传新脚本
    sftp = ssh.open_sftp()
    remote_path = "D:/VideoTranscode/scripts/watcher.ps1"
    print(f"上传英文版脚本到 {remote_path}...")
    
    with sftp.file(remote_path, 'w') as f:
        f.write(script_content)
    
    sftp.close()
    
    # 验证
    print("\n验证脚本前10行:")
    stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "Get-Content \'{remote_path}\' | Select-Object -First 10"')
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 测试语法
    print("\n测试脚本语法:")
    stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "Test-Path \'{remote_path}\'; $null = [System.Management.Automation.Language.Parser]::ParseFile(\'{remote_path}\', [ref]$null, [ref]$errors); if ($errors.Count -eq 0) {{ Write-Host \'Syntax OK\' }} else {{ $errors | ForEach-Object {{ Write-Host $_.Message }} }}"')
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')
    print(output)
    if error:
        print(f"Error: {error}")
    
    ssh.close()
    print("\n部署完成!")

if __name__ == "__main__":
    deploy()
