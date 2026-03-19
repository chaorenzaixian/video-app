"""
通过 SQLite 更新下载页配置
"""
import paramiko
import json

# 服务器配置
SERVER_HOST = "38.47.218.230"
SERVER_USER = "root"
SERVER_KEY = "server_key_main"

# 数据库路径
DB_PATH = "/www/wwwroot/video-app/backend/app.db"

# 新的下载链接
APK_URL = "http://38.47.218.230/Soul.apk"
MOBILECONFIG_URL = "http://38.47.218.230/Soul.mobileconfig"

def create_ssh_client():
    """创建 SSH 连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"连接服务器 {SERVER_HOST}...")
    ssh.connect(
        hostname=SERVER_HOST,
        username=SERVER_USER,
        key_filename=SERVER_KEY,
        timeout=30
    )
    print("连接成功！")
    return ssh

def run_sqlite_cmd(ssh, sql):
    """执行 SQLite 命令"""
    cmd = f'sqlite3 {DB_PATH} "{sql}"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        print(f"错误: {error}")
    return result

def update_config(ssh):
    """更新下载页配置"""
    print("\n=== 更新下载页配置 ===")
    
    # Android 链接 JSON
    android_links = json.dumps([{
        "id": "main",
        "name": "主下载",
        "url": APK_URL,
        "is_primary": True,
        "is_active": True,
        "sort_order": 0
    }])
    
    # 转义单引号
    android_links_escaped = android_links.replace("'", "''")
    
    configs = [
        ("download_android_links", android_links_escaped, "Android 下载链接列表"),
        ("download_ios_mobileconfig", MOBILECONFIG_URL, "iOS mobileconfig 链接"),
        ("download_ios_mobileconfig_active", "true", "mobileconfig 链接启用状态"),
    ]
    
    for key, value, desc in configs:
        # 先检查是否存在
        check_sql = f"SELECT COUNT(*) FROM system_config WHERE key='{key}';"
        result = run_sqlite_cmd(ssh, check_sql)
        count = int(result.strip()) if result.strip().isdigit() else 0
        
        if count > 0:
            # 更新
            sql = f"UPDATE system_config SET value='{value}' WHERE key='{key}';"
            print(f"更新 {key}...")
        else:
            # 插入
            sql = f"INSERT INTO system_config (key, value, group_name, description) VALUES ('{key}', '{value}', 'download_page', '{desc}');"
            print(f"插入 {key}...")
        
        run_sqlite_cmd(ssh, sql)
    
    print("配置更新完成！")

def verify_config(ssh):
    """验证配置"""
    print("\n=== 验证配置 ===")
    sql = "SELECT key, value FROM system_config WHERE key LIKE 'download_%';"
    result = run_sqlite_cmd(ssh, sql)
    print(result)

def main():
    print("=" * 50)
    print("更新下载页配置 (SQLite)")
    print("=" * 50)
    
    try:
        ssh = create_ssh_client()
        
        # 检查表是否存在
        print("\n检查 system_config 表...")
        result = run_sqlite_cmd(ssh, ".tables")
        print(f"数据库表: {result}")
        
        # 更新配置
        update_config(ssh)
        
        # 验证
        verify_config(ssh)
        
        ssh.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    print(f"\nAPK 下载地址: {APK_URL}")
    print(f"Mobileconfig 下载地址: {MOBILECONFIG_URL}")

if __name__ == "__main__":
    main()
