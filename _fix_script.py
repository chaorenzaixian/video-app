# 重新上传修复后的脚本
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print(f"连接转码服务器 {HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    
    print("连接成功！")
    
    # 读取本地脚本并用 UTF-8 BOM 编码上传
    with open("scripts/watcher_complete.ps1", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 上传脚本 (使用 UTF-8 with BOM)
    sftp = ssh.open_sftp()
    remote_path = "D:/VideoTranscode/scripts/watcher.ps1"
    
    with sftp.open(remote_path, 'wb') as f:
        # 写入 UTF-8 BOM
        f.write(b'\xef\xbb\xbf')
        f.write(content.encode('utf-8'))
    
    print(f"已上传: {remote_path}")
    
    sftp.close()
    ssh.close()
    print("完成！请重新运行启动脚本")

if __name__ == "__main__":
    main()
