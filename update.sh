#!/bin/bash
# 一键更新部署脚本
# 用法: ./update.sh [frontend|backend|all]

set -e
cd "$(dirname "$0")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
error() { echo -e "${RED}[错误]${NC} $1"; exit 1; }

# 备份当前版本
backup() {
    BACKUP_DIR="backups/$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "$BACKUP_DIR"
    cp -r backend/app.db "$BACKUP_DIR/" 2>/dev/null || true
    cp -r backend/.env "$BACKUP_DIR/" 2>/dev/null || true
    log "已备份到 $BACKUP_DIR"
}

# 拉取最新代码
pull_code() {
    log "拉取最新代码..."
    git stash 2>/dev/null || true
    git pull origin main
    git stash pop 2>/dev/null || true
}

# 更新前端
update_frontend() {
    log "更新前端..."
    cd frontend
    npm install --production=false
    npm run build
    cd ..
    log "前端更新完成"
}

# 更新后端
update_backend() {
    log "更新后端..."
    cd backend
    source venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null || true
    pip install -r requirements.txt -q
    cd ..
    
    # 重启后端服务
    if systemctl is-active --quiet video-backend; then
        systemctl restart video-backend
        log "后端服务已重启"
    elif pm2 list | grep -q "video-backend"; then
        pm2 restart video-backend
        log "后端服务已重启 (PM2)"
    else
        warn "请手动重启后端服务"
    fi
}

# 重载 Nginx
reload_nginx() {
    if systemctl is-active --quiet nginx; then
        nginx -t && systemctl reload nginx
        log "Nginx 已重载"
    fi
}

# 主流程
main() {
    MODE=${1:-all}
    
    log "========== 开始更新 =========="
    backup
    pull_code
    
    case $MODE in
        frontend)
            update_frontend
            reload_nginx
            ;;
        backend)
            update_backend
            ;;
        all|*)
            update_frontend
            update_backend
            reload_nginx
            ;;
    esac
    
    log "========== 更新完成 =========="
    log "访问网站检查是否正常"
}

main "$@"
