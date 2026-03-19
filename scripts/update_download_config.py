"""
更新下载页配置，应用新上传的文件链接
"""
import os
import paramiko

# 服务器配置
SERVER_HOST = "38.47.218.230"
SERVER_USER = "root"
SERVER_KEY = "server_key_main"
API_HOST = "38.47.218.230"
API_PORT = 8000

# 新的下载链接
APK_URL = "http://38.47.218.230/Soul.apk"
MOBILECONFIG_URL = "http://38.47.218.230/Soul.mobileconfig"

def create_ssh_client():
    """创建 SSH 连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), SERVER_KEY)
    
    print(f"连接服务器 {SERVER_HOST}...")
    ssh.connect(
        hostname=SERVER_HOST,
        username=SERVER_USER,
        key_filename=key_path,
        timeout=30
    )
    print("连接成功！")
    return ssh

def update_config_via_db(ssh):
    """通过数据库直接更新配置"""
    print("\n更新下载页配置...")
    
    # 更新 Android 下载链接
    android_links = f'[{{"id": "main", "name": "主下载", "url": "{APK_URL}", "is_primary": true, "is_active": true, "sort_order": 0}}]'
    
    # 使用 sqlite3 更新配置 (如果是 SQLite)
    # 或者使用 psql 更新 (如果是 PostgreSQL)
    
    # 先检查数据库类型
    stdin, stdout, stderr = ssh.exec_command("cat /www/wwwroot/video-api/backend/.env | grep DATABASE")
    db_config = stdout.read().decode()
    print(f"数据库配置: {db_config[:100]}...")
    
    if "postgresql" in db_config.lower() or "postgres" in db_config.lower():
        # PostgreSQL
        print("检测到 PostgreSQL 数据库")
        
        # 更新 Android 链接
        cmd = f'''psql -U postgres -d video_app -c "UPDATE system_config SET value = '{android_links}' WHERE key = 'download_android_links';"'''
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode()
        error = stderr.read().decode()
        if error and "ERROR" in error:
            print(f"更新 Android 链接失败: {error}")
        else:
            print(f"Android 链接更新: {result.strip()}")
        
        # 更新 mobileconfig 链接
        cmd = f'''psql -U postgres -d video_app -c "UPDATE system_config SET value = '{MOBILECONFIG_URL}' WHERE key = 'download_ios_mobileconfig';"'''
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode()
        error = stderr.read().decode()
        if error and "ERROR" in error:
            print(f"更新 mobileconfig 链接失败: {error}")
        else:
            print(f"Mobileconfig 链接更新: {result.strip()}")
        
        # 如果记录不存在，则插入
        cmd = f'''psql -U postgres -d video_app -c "INSERT INTO system_config (key, value, group_name, description) VALUES ('download_android_links', '{android_links}', 'download_page', 'Android 下载链接列表') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"'''
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode()
        print(f"Android 链接 upsert: {result.strip()}")
        
        cmd = f'''psql -U postgres -d video_app -c "INSERT INTO system_config (key, value, group_name, description) VALUES ('download_ios_mobileconfig', '{MOBILECONFIG_URL}', 'download_page', 'iOS mobileconfig 链接') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"'''
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode()
        print(f"Mobileconfig 链接 upsert: {result.strip()}")
        
        # 启用 mobileconfig
        cmd = f'''psql -U postgres -d video_app -c "INSERT INTO system_config (key, value, group_name, description) VALUES ('download_ios_mobileconfig_active', 'true', 'download_page', 'mobileconfig 链接启用状态') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"'''
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode()
        print(f"Mobileconfig 启用状态: {result.strip()}")
        
    else:
        print("未检测到 PostgreSQL，尝试使用 API 更新...")
        return False
    
    return True

def verify_config(ssh):
    """验证配置是否更新成功"""
    print("\n验证配置...")
    
    cmd = '''psql -U postgres -d video_app -c "SELECT key, value FROM system_config WHERE key LIKE 'download_%' ORDER BY key;"'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode()
    print(result)

def main():
    print("=" * 50)
    print("更新下载页配置")
    print("=" * 50)
    
    try:
        ssh = create_ssh_client()
        
        # 更新配置
        success = update_config_via_db(ssh)
        
        if success:
            # 验证
            verify_config(ssh)
        
        ssh.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("配置更新完成！")
    print("=" * 50)
    print("\n下载地址已更新为:")
    print(f"  APK: {APK_URL}")
    print(f"  Mobileconfig: {MOBILECONFIG_URL}")

if __name__ == "__main__":
    main()
