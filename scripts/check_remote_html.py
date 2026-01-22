"""检查远程HTML文件"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查文件行数
stdin, stdout, stderr = ssh.exec_command('powershell "(Get-Content D:\\VideoTranscode\\service\\templates\\index.html).Count"', timeout=30)
lines = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"远程文件行数: {lines}")

# 检查是否包含addLocalFile
stdin, stdout, stderr = ssh.exec_command('findstr "addLocalFile" D:\\VideoTranscode\\service\\templates\\index.html', timeout=30)
result = stdout.read().decode('gbk', errors='ignore')
print(f"包含addLocalFile: {'是' if 'addLocalFile' in result else '否'}")

# 检查文件大小
stdin, stdout, stderr = ssh.exec_command('powershell "(Get-Item D:\\VideoTranscode\\service\\templates\\index.html).Length"', timeout=30)
size = stdout.read().decode('utf-8', errors='ignore').strip()
print(f"远程文件大小: {size} 字节")

ssh.close()

# 本地文件信息
import os
local_size = os.path.getsize('transcode_service/templates/index.html')
with open('transcode_service/templates/index.html', 'r', encoding='utf-8') as f:
    local_lines = len(f.readlines())
print(f"本地文件行数: {local_lines}")
print(f"本地文件大小: {local_size} 字节")
