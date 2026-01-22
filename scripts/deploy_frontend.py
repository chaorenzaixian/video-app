"""
部署前端到主服务器
"""
import paramiko
import os

def main():
    print("连接主服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 读取密钥
    key_path = 'server_key_main'
    if os.path.exists(key_path):
        key = paramiko.Ed25519Key.from_private_key_file(key_path)
        client.connect('38.47.218.137', username='root', pkey=key)
    else:
        print("密钥文件不存在，请手动上传")
        return
    
    sftp = client.open_sftp()
    
    local_dir = 'frontend/dist'
    remote_dir = '/var/www/video-admin'
    
    def upload_dir(local, remote):
        # 确保远程目录存在
        try:
            sftp.stat(remote)
        except:
            try:
                sftp.mkdir(remote)
            except:
                pass
        
        for item in os.listdir(local):
            local_path = os.path.join(local, item)
            remote_path = f"{remote}/{item}"
            
            if os.path.isfile(local_path):
                print(f"  上传: {item}")
                sftp.put(local_path, remote_path)
            elif os.path.isdir(local_path):
                try:
                    sftp.mkdir(remote_path)
                except:
                    pass
                upload_dir(local_path, remote_path)
    
    print(f"上传 {local_dir} -> {remote_dir}")
    upload_dir(local_dir, remote_dir)
    
    sftp.close()
    client.close()
    print("\n✓ 部署完成!")

if __name__ == '__main__':
    main()
