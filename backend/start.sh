#!/bin/bash
cd /www/wwwroot/video-app/backend

# 停止现有进程
pkill -f "run.py" 2>/dev/null
fuser -k 8000/tcp 2>/dev/null
sleep 2

# 以www用户启动
su -s /bin/bash -c "cd /www/wwwroot/video-app/backend && nohup /www/wwwroot/video-app/backend/61196a672dfc27ae6c4fbd8bc3448ba3_venv/bin/python3 run.py > logs/app.log 2>&1 &" www

echo "Backend started as www user"
