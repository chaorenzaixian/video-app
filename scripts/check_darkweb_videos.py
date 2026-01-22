"""检查主服务器上的暗网视频"""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 使用密钥连接
key = paramiko.Ed25519Key.from_private_key_file('server_key_main')
client.connect('38.47.218.137', username='root', pkey=key)

# 列出所有表
cmd = '''sqlite3 /www/wwwroot/video-app/backend/app.db ".tables"'''

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
tables = stdout.read().decode('utf-8')
print("All tables:")
print(tables)

# 查找darkweb相关的表
for t in tables.split():
    if 'dark' in t.lower():
        print(f"Found darkweb table: {t}")

client.close()
