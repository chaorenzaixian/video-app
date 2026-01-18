# deploy_direct_upload.py - 部署直接上传功能到主服务器
import paramiko
import os

MAIN_SERVER = "38.47.218.137"
MAIN_USER = "root"
KEY_FILE = "server_key_new"

def main():
    print("=" * 50)
    print("部署直接上传功能到主服务器")
    print("=" * 50)
    
    # 连接主服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    key = paramiko.RSAKey.from_private_key_file(KEY_FILE)
    ssh.connect(MAIN_SERVER, username=MAIN_USER, pkey=key)
    print("连接成功!")
    
    sftp = ssh.open_sftp()
    
    # 1. 上传 windows_transcode_service.py
    print("\n1. 上传 windows_transcode_service.py...")
    local_path = "backend/app/services/windows_transcode_service.py"
    remote_path = "/www/wwwroot/video-app/backend/app/services/windows_transcode_service.py"
    sftp.put(local_path, remote_path)
    print(f"  完成: {remote_path}")
    
    # 2. 上传更新后的 videos.py
    print("\n2. 上传更新后的 videos.py...")
    local_path = "backend/app/api/videos.py"
    remote_path = "/www/wwwroot/video-app/backend/app/api/videos.py"
    sftp.put(local_path, remote_path)
    print(f"  完成: {remote_path}")
    
    # 3. 安装 aiohttp（如果没有）
    print("\n3. 检查/安装 aiohttp...")
    stdin, stdout, stderr = ssh.exec_command(
        'cd /www/wwwroot/video-app/backend && source venv/bin/activate && pip install aiohttp'
    )
    stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "  aiohttp 已安装")
    
    # 4. 添加环境变量配置
    print("\n4. 检查环境变量...")
    stdin, stdout, stderr = ssh.exec_command(
        'grep -q "DIRECT_UPLOAD_ENABLED" /www/wwwroot/video-app/backend/.env || echo -e "\\n# 转码服务器直接上传\\nDIRECT_UPLOAD_ENABLED=true\\nTRANSCODE_SERVER_HOST=198.176.60.121\\nTRANSCODE_SERVER_PORT=5000\\nTRANSCODE_API_KEY=vYTWoms4FKOqySca1jCLtNHRVz3BAI6U" >> /www/wwwroot/video-app/backend/.env'
    )
    stdout.channel.recv_exit_status()
    print("  环境变量已配置")
    
    # 5. 重启后端服务
    print("\n5. 重启后端服务...")
    stdin, stdout, stderr = ssh.exec_command(
        'supervisorctl restart video-backend || systemctl restart video-backend || (cd /www/wwwroot/video-app/backend && pkill -f "uvicorn" && source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &)'
    )
    stdout.channel.recv_exit_status()
    print("  服务已重启")
    
    sftp.close()
    ssh.close()
    
    print("\n" + "=" * 50)
    print("部署完成!")
    print("=" * 50)
    print("\n新的上传流程:")
    print("  浏览器 → 转码服务器(198.176.60.121:5000) → 转码 → 主服务器")
    print("\n注意: 需要先在转码服务器上启动上传服务:")
    print("  python D:\\VideoTranscode\\scripts\\upload_server.py")

if __name__ == "__main__":
    main()
