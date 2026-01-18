#!/bin/bash
# GPU 服务器视频管理工具
# 功能：下载视频、转码、上传到主服务器

WORK_DIR="$HOME/video-transcode"
DOWNLOAD_DIR="$WORK_DIR/downloads"
UPLOAD_DIR="$WORK_DIR/uploads"
LOG_DIR="$WORK_DIR/logs"

# 主服务器配置
MAIN_SERVER="root@38.47.218.137"
MAIN_API="http://38.47.218.137:8000"
TRANSCODE_KEY="vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"

mkdir -p "$DOWNLOAD_DIR" "$UPLOAD_DIR" "$LOG_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
error() { echo -e "${RED}[错误]${NC} $1"; }

# ========== 下载功能 ==========
download_video() {
    local url="$1"
    local filename="$2"
    
    if [ -z "$url" ]; then
        echo "用法: $0 download <URL> [文件名]"
        echo ""
        echo "支持的下载方式:"
        echo "  - 直接链接: https://example.com/video.mp4"
        echo "  - YouTube: https://youtube.com/watch?v=xxx (需要 yt-dlp)"
        echo "  - 其他视频网站 (需要 yt-dlp)"
        return 1
    fi
    
    # 自动生成文件名
    if [ -z "$filename" ]; then
        filename="video_$(date +%Y%m%d_%H%M%S).mp4"
    fi
    
    local output_path="$DOWNLOAD_DIR/$filename"
    
    log "开始下载: $url"
    log "保存到: $output_path"
    
    # 判断是否需要 yt-dlp
    if [[ "$url" == *"youtube.com"* ]] || [[ "$url" == *"youtu.be"* ]] || [[ "$url" == *"twitter.com"* ]] || [[ "$url" == *"tiktok.com"* ]]; then
        if command -v yt-dlp &> /dev/null; then
            yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
                -o "$output_path" "$url"
        else
            error "需要安装 yt-dlp: sudo pip install yt-dlp"
            return 1
        fi
    else
        # 普通下载
        if command -v aria2c &> /dev/null; then
            aria2c -x 16 -s 16 -d "$DOWNLOAD_DIR" -o "$filename" "$url"
        else
            wget -O "$output_path" "$url"
        fi
    fi
    
    if [ -f "$output_path" ]; then
        local size=$(du -h "$output_path" | cut -f1)
        log "下载完成: $filename ($size)"
        echo "$output_path"
    else
        error "下载失败"
        return 1
    fi
}

# ========== 转码功能 ==========
transcode_video() {
    local input="$1"
    local video_id="$2"
    
    if [ -z "$input" ]; then
        echo "用法: $0 transcode <视频文件> [video_id]"
        echo ""
        echo "示例:"
        echo "  $0 transcode downloads/video.mp4"
        echo "  $0 transcode downloads/video.mp4 123"
        return 1
    fi
    
    # 检查文件
    if [ ! -f "$input" ]; then
        # 尝试在 downloads 目录找
        if [ -f "$DOWNLOAD_DIR/$input" ]; then
            input="$DOWNLOAD_DIR/$input"
        else
            error "文件不存在: $input"
            return 1
        fi
    fi
    
    # 自动生成 video_id
    if [ -z "$video_id" ]; then
        video_id=$(date +%s)
        warn "未指定 video_id，自动生成: $video_id"
    fi
    
    log "开始转码: $input (video_id=$video_id)"
    
    # 调用转码脚本
    "$WORK_DIR/transcode.sh" process "$video_id" "$input"
}

# ========== 上传功能 ==========
upload_video() {
    local input="$1"
    local title="$2"
    
    if [ -z "$input" ]; then
        echo "用法: $0 upload <视频文件> [标题]"
        return 1
    fi
    
    if [ ! -f "$input" ]; then
        if [ -f "$DOWNLOAD_DIR/$input" ]; then
            input="$DOWNLOAD_DIR/$input"
        else
            error "文件不存在: $input"
            return 1
        fi
    fi
    
    if [ -z "$title" ]; then
        title=$(basename "$input" | sed 's/\.[^.]*$//')
    fi
    
    local filename=$(basename "$input")
    local video_id=$(date +%s)
    
    log "上传视频到主服务器..."
    log "文件: $input"
    log "标题: $title"
    
    # 1. 先上传原始文件到主服务器
    rsync -avz --progress "$input" \
        "$MAIN_SERVER:/www/wwwroot/video-app/backend/uploads/videos/"
    
    if [ $? -eq 0 ]; then
        log "文件上传成功"
        
        # 2. 本地转码
        log "开始 GPU 转码..."
        "$WORK_DIR/transcode.sh" process "$video_id" "$input"
        
        log "完成！视频已处理并上传"
    else
        error "上传失败"
        return 1
    fi
}

# ========== 列出文件 ==========
list_files() {
    echo -e "${BLUE}=== 下载目录 ===${NC}"
    ls -lh "$DOWNLOAD_DIR" 2>/dev/null || echo "  (空)"
    echo ""
    echo -e "${BLUE}=== 待处理 ===${NC}"
    ls -lh "$UPLOAD_DIR" 2>/dev/null || echo "  (空)"
}

# ========== 快速处理 ==========
quick_process() {
    local url="$1"
    local title="$2"
    
    if [ -z "$url" ]; then
        echo "用法: $0 quick <URL> [标题]"
        echo ""
        echo "一键完成: 下载 → 转码 → 上传"
        return 1
    fi
    
    log "=== 快速处理模式 ==="
    
    # 1. 下载
    local filename="quick_$(date +%Y%m%d_%H%M%S).mp4"
    local filepath=$(download_video "$url" "$filename")
    
    if [ -z "$filepath" ] || [ ! -f "$filepath" ]; then
        error "下载失败，终止"
        return 1
    fi
    
    # 2. 上传并转码
    upload_video "$filepath" "$title"
}

# ========== GPU 状态 ==========
gpu_status() {
    echo -e "${BLUE}=== GPU 状态 ===${NC}"
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu \
        --format=csv,noheader 2>/dev/null || echo "无法获取 GPU 信息"
    
    echo ""
    echo -e "${BLUE}=== 转码进程 ===${NC}"
    ps aux | grep -E "(ffmpeg|transcode)" | grep -v grep || echo "  无转码任务"
    
    echo ""
    echo -e "${BLUE}=== 监控服务 ===${NC}"
    if pgrep -f "watch_service" > /dev/null; then
        echo -e "  ${GREEN}运行中${NC}"
    else
        echo -e "  ${RED}未运行${NC} (启动: ./watch_service.sh start)"
    fi
}

# ========== 主菜单 ==========
show_menu() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   GPU 视频管理工具                 ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════╝${NC}"
    echo ""
    echo "命令:"
    echo "  download <URL> [文件名]    - 下载视频"
    echo "  transcode <文件> [ID]      - GPU 转码"
    echo "  upload <文件> [标题]       - 上传到主服务器"
    echo "  quick <URL> [标题]         - 一键处理(下载+转码+上传)"
    echo "  list                       - 列出文件"
    echo "  status                     - GPU 状态"
    echo ""
    echo "示例:"
    echo "  $0 download https://example.com/video.mp4"
    echo "  $0 quick https://example.com/video.mp4 \"我的视频\""
    echo ""
}

# ========== 主入口 ==========
case "$1" in
    download|d)
        download_video "$2" "$3"
        ;;
    transcode|t)
        transcode_video "$2" "$3"
        ;;
    upload|u)
        upload_video "$2" "$3"
        ;;
    quick|q)
        quick_process "$2" "$3"
        ;;
    list|ls|l)
        list_files
        ;;
    status|s)
        gpu_status
        ;;
    *)
        show_menu
        ;;
esac
