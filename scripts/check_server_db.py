"""检查服务器数据库配置"""
import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('38.47.218.230', username='root', key_filename='server_key_main')

# 查找后端目录
print("=== 查找后端目录 ===")
stdin, stdout, stderr = ssh.exec_command('ls -la /www/wwwroot/')
print(stdout.read().decode())

# 查找 .env 文件
print("=== 查找 .env 文件 ===")
stdin, stdout, stderr = ssh.exec_command('find /www -name ".env" 2>/dev/null')
print(stdout.read().decode())

# 检查数据库
print("=== 检查 PostgreSQL ===")
stdin, stdout, stderr = ssh.exec_command('systemctl status postgresql 2>/dev/null || echo "PostgreSQL not running"')
print(stdout.read().decode()[:500])

# 检查 SQLite
print("=== 查找 SQLite 数据库 ===")
stdin, stdout, stderr = ssh.exec_command('find /www -name "*.db" 2>/dev/null')
print(stdout.read().decode())

ssh.close()
