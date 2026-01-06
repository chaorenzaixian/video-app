# 同步到服务器脚本
# 使用前修改服务器信息

$SERVER = "root@你的服务器IP"
$REMOTE_PATH = "/www/video-app"

# 同步后端
Write-Host "同步后端代码..." -ForegroundColor Cyan
rsync -avz --delete `
  --exclude 'venv' `
  --exclude '__pycache__' `
  --exclude '*.pyc' `
  --exclude '.env' `
  --exclude 'app.db' `
  --exclude 'uploads' `
  --exclude 'logs' `
  ./backend/ ${SERVER}:${REMOTE_PATH}/backend/

# 同步前端（构建后）
Write-Host "构建前端..." -ForegroundColor Cyan
Set-Location frontend
npm run build
Set-Location ..

Write-Host "同步前端dist..." -ForegroundColor Cyan
rsync -avz --delete ./frontend/dist/ ${SERVER}:${REMOTE_PATH}/frontend/dist/

Write-Host "重启服务..." -ForegroundColor Cyan
ssh $SERVER "cd ${REMOTE_PATH} && pm2 restart all"

Write-Host "同步完成!" -ForegroundColor Green
