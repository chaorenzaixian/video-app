#!/bin/bash
# 媒体文件同步脚本 - 将本地上传文件同步到媒体服务器
# 用法: ./sync_media.sh [--full]  (--full 表示全量同步)

# 配置
MEDIA_SERVER_IP="104.143.33.52"
MEDIA_SERVER_USER="root"
MEDIA_SERVER_PASS="ZnkyFjJTWNwFK3wp"
MEDIA_SERVER_PATH="/www/wwwroot/media"
LOCAL_UPLOAD_DIR="/www/wwwroot/video-app/backend/uploads"

# 日志
LOG_FILE="/www/wwwroot/video-app/backend/logs/sync_media.log"
mkdir -p $(dirname $LOG_FILE)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 使用 rsync + sshpass 同步
sync_files() {
    local src_dir=$1
    local dest_dir=$2
    local dir_name=$(basename $src_dir)
    
    log "开始同步: $dir_name"
    
    sshpass -p "$MEDIA_SERVER_PASS" rsync -avz --progress \
        -e "ssh -o StrictHostKeyChecking=no" \
        "$src_dir/" \
        "${MEDIA_SERVER_USER}@${MEDIA_SERVER_IP}:${MEDIA_SERVER_PATH}/${dest_dir}/" \
        2>&1 | tail -5 >> $LOG_FILE
    
    if [ $? -eq 0 ]; then
        log "同步完成: $dir_name"
    else
        log "同步失败: $dir_name"
    fi
}

# 主逻辑
log "========== 开始媒体同步 =========="

# 同步各目录
sync_files "$LOCAL_UPLOAD_DIR/hls" "hls"
sync_files "$LOCAL_UPLOAD_DIR/thumbnails" "uploads/covers"
sync_files "$LOCAL_UPLOAD_DIR/videos" "uploads/videos"
sync_files "$LOCAL_UPLOAD_DIR/images" "uploads/images"
sync_files "$LOCAL_UPLOAD_DIR/previews" "uploads/previews"

log "========== 媒体同步完成 =========="

