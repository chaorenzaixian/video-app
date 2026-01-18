#!/usr/bin/env python3
"""应用视频优化配置"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_USER = 'root'
SSH_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("应用视频优化配置...")
print("=" * 60)

# 优化后的 nginx 配置
nginx_config = '''server {
    listen 80 default_server;
    server_name _;
    root /www/wwwroot/video-app/frontend/dist;
    index index.html;

    # 启用 sendfile 和 aio 优化大文件传输
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    
    # 增加输出缓冲区
    output_buffers 1 512k;
    
    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets {
        alias /www/wwwroot/video-app/frontend/dist/assets;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /images {
        alias /www/wwwroot/video-app/frontend/dist/images;
        expires 30d;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 500M;
    }

    # 视频文件优化配置
    location /uploads {
        alias /www/wwwroot/video-app/backend/uploads;
        expires 7d;
        add_header Cache-Control "public";
        
        # 支持断点续传
        add_header Accept-Ranges bytes;
        
        # 视频文件特殊处理
        location ~* \\.(mp4|webm|m3u8|ts)$ {
            expires 7d;
            add_header Cache-Control "public";
            add_header Accept-Ranges bytes;
            
            # 允许跨域
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, OPTIONS";
        }
        
        # 图片缓存更长时间
        location ~* \\.(jpg|jpeg|png|gif|webp)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    location /static {
        alias /www/wwwroot/video-app/backend/static;
        expires 30d;
    }
}
'''

print("1. 更新 Nginx 配置...")
# 备份原配置
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cp /www/server/panel/vhost/nginx/0.default.conf /www/server/panel/vhost/nginx/0.default.conf.bak"'
ssh.exec_command(cmd, timeout=60)

# 写入新配置
cmd = f'''ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cat > /www/server/panel/vhost/nginx/0.default.conf << 'NGINX_EOF'
{nginx_config}
NGINX_EOF"'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print(f"写入配置错误: {err}")

# 测试配置
print("\n2. 测试 Nginx 配置...")
cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "nginx -t"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
output = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(output + err)

if 'successful' in err or 'successful' in output:
    # 重载配置
    print("\n3. 重载 Nginx...")
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "nginx -s reload"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    print("Nginx 已重载")
else:
    print("配置测试失败，恢复备份...")
    cmd = f'ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {MAIN_USER}@{MAIN_HOST} "cp /www/server/panel/vhost/nginx/0.default.conf.bak /www/server/panel/vhost/nginx/0.default.conf"'
    ssh.exec_command(cmd, timeout=60)

ssh.close()
print("\n完成!")
