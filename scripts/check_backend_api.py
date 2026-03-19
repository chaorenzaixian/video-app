"""检查后端 API 和数据库"""
import paramiko
import requests

# 服务器配置
SERVER_HOST = "38.47.218.230"
SERVER_USER = "root"
SERVER_KEY = "server_key_main"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_HOST, username=SERVER_USER, key_filename=SERVER_KEY)

# 检查后端进程
print("=== 检查后端进程 ===")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep -E "uvicorn|python.*main" | grep -v grep')
print(stdout.read().decode())

# 检查 .env 文件
print("=== 检查 .env 配置 ===")
stdin, stdout, stderr = ssh.exec_command('cat /www/wwwroot/video-app/backend/.env')
env_content = stdout.read().decode()
print(env_content[:1000] if env_content else "(空)")

# 检查数据库表
print("\n=== 检查数据库表 ===")
stdin, stdout, stderr = ssh.exec_command('sqlite3 /www/wwwroot/video-app/backend/app.db ".schema system_config"')
print(stdout.read().decode() or "(表不存在)")

# 检查所有表
print("\n=== 所有数据库表 ===")
stdin, stdout, stderr = ssh.exec_command('sqlite3 /www/wwwroot/video-app/backend/app.db ".tables"')
print(stdout.read().decode())

ssh.close()

# 测试 API
print("\n=== 测试 API ===")
try:
    resp = requests.get(f"http://{SERVER_HOST}:8000/api/v1/download-page/config", timeout=10)
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        import json
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500])
except Exception as e:
    print(f"API 请求失败: {e}")
