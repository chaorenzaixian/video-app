"""
部署 direct-publish API 到主服务器
"""
import paramiko
import os

def main():
    # 读取本地文件
    local_file = "backend/app/api/admin_video_ops.py"
    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 连接主服务器
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key_path = "server_key_new"
    pkey = paramiko.Ed25519Key.from_private_key_file(key_path)
    client.connect('38.47.218.137', username='root', pkey=pkey)
    
    print("=== 上传文件 ===")
    sftp = client.open_sftp()
    remote_path = "/www/wwwroot/video-app/backend/app/api/admin_video_ops.py"
    
    # 备份原文件
    try:
        sftp.rename(remote_path, remote_path + ".bak")
        print("已备份原文件")
    except:
        pass
    
    # 上传新文件
    with sftp.file(remote_path, 'w') as f:
        f.write(content)
    print(f"已上传: {remote_path}")
    sftp.close()
    
    print("\n=== 重启后端服务 ===")
    stdin, stdout, stderr = client.exec_command('supervisorctl restart video-api')
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    # 等待服务启动
    import time
    time.sleep(3)
    
    print("\n=== 检查服务状态 ===")
    stdin, stdout, stderr = client.exec_command('supervisorctl status video-api')
    print(stdout.read().decode())
    
    print("\n=== 测试API ===")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8000/api/v1/videos/categories/by-type?category_type=video | head -c 200')
    print(stdout.read().decode())
    
    client.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
