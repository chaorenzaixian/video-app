# 部署指南

## 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- FFmpeg (视频处理)

## 服务器配置

### 当前生产服务器
- IP: `38.47.218.137`
- SSH: `ssh -i server_key_new root@38.47.218.137`

### 目录结构
```
/www/wwwroot/video-app/
├── backend/          # 后端代码
│   ├── venv/         # Python虚拟环境
│   ├── uploads/      # 上传文件
│   └── logs/         # 日志文件
├── frontend/         # 前端代码
└── flutter/          # Flutter应用
```

## 部署流程

### 1. 更新代码
```bash
cd /www/wwwroot/video-app
git pull origin main
```

### 2. 后端部署
```bash
cd backend
source venv/bin/activate

# 安装依赖（如有更新）
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 重启服务
systemctl restart video-app-backend
```

### 3. 前端部署
```bash
cd frontend
npm install
npm run build

# 复制到Nginx目录
cp -r dist/* /www/wwwroot/video-app-frontend/
```

### 4. 查看日志
```bash
# 后端日志
journalctl -u video-app-backend -f

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Systemd 服务配置

### 后端服务 (`/etc/systemd/system/video-app-backend.service`)
```ini
[Unit]
Description=Video App Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/video-app/backend
Environment=PATH=/www/wwwroot/video-app/backend/venv/bin
ExecStart=/www/wwwroot/video-app/backend/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 服务管理命令
```bash
# 启动
systemctl start video-app-backend

# 停止
systemctl stop video-app-backend

# 重启
systemctl restart video-app-backend

# 查看状态
systemctl status video-app-backend

# 开机自启
systemctl enable video-app-backend
```

## 数据库

### PostgreSQL 配置
- 用户: `video_app`
- 密码: `VideoApp2024!`
- 数据库: `video_app`

### 连接命令
```bash
psql -U video_app -d video_app -h localhost
```

### 备份
```bash
pg_dump -U video_app video_app > backup_$(date +%Y%m%d).sql
```

### 恢复
```bash
psql -U video_app video_app < backup_20260113.sql
```

## Redis

### 连接
```bash
redis-cli
```

### 清除缓存
```bash
redis-cli FLUSHDB
```

## Nginx 配置

配置文件: `/etc/nginx/conf.d/video-app.conf`

```nginx
server {
    listen 80;
    server_name 38.47.218.137;

    # 前端
    location / {
        root /www/wwwroot/video-app-frontend;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 上传文件
    location /uploads {
        alias /www/wwwroot/video-app/backend/uploads;
    }
}
```

## Celery Worker (可选)

### 启动 Worker
```bash
cd /www/wwwroot/video-app/backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### 启动 Beat (定时任务)
```bash
celery -A app.core.celery_app beat --loglevel=info
```

## 监控

### 健康检查
```bash
curl http://localhost:8001/api/v1/admin/monitoring/health
```

### 性能指标
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/v1/admin/monitoring/metrics
```

## 故障排查

### 服务无法启动
1. 检查日志: `journalctl -u video-app-backend -n 100`
2. 检查端口: `netstat -tlnp | grep 8001`
3. 检查数据库连接: `psql -U video_app -d video_app -c "SELECT 1"`

### 数据库连接失败
1. 检查 PostgreSQL 状态: `systemctl status postgresql`
2. 检查连接配置: `cat backend/.env`

### Redis 连接失败
1. 检查 Redis 状态: `systemctl status redis`
2. 测试连接: `redis-cli ping`
