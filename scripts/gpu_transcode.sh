#!/bin/bash
# GPU 视频转码脚本
# 部署位置: GPU服务器 ~/video-transcode/transcode.sh

set -e

# ========== 配置 ==========
WORK_DIR="$HOME/video-transcode"
UPLOAD_DIR="$WORK_DIR/uploads"
PROCESSED_DIR="$WORK_DIR/processed"
LOG_DIR="$WORK_DIR/logs"
LOG_FILE="$LOG_DIR/transcode_$(date +%Y%m%d).log"

# 主服务器配置
MAIN_SERVER="root@38.47.218.137"
MAIN_PROJECT="/www/wwwroot/video-app"
MAIN_UPLOAD_DIR="$MAIN_PROJECT/backend/uploads"

# GPU 编码参数
GPU_PRESET="p4"  # NVENC preset: p1(最快)-p7(最慢最好)
GPU_CQ="23"      # 质量参数 (18-28, 越小越好)

# ========== 函数 ==========
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 生成缩略图 (CPU - 够快)
generate_thumbnail() {
    local video_id=$1
    local input_file=$2
    local duration=$3
    local output_dir="$PROCESSED_DIR/$video_id/thumbnails"
    mkdir -p "$output_dir"
    
    log "[Thumbnail] 开始生成缩略图: video_id=$video_id"
    
    # 智能选帧: 5个采样点
    local best_score=0
    local best_time=1
    
    for pct in 10 25 40 55 70; do
        local time=$(echo "$duration * $pct / 100" | bc -l)
        local temp_file="$output_dir/temp_$pct.webp"
        
        ffmpeg -ss "$time" -i "$input_file" -vframes 1 \
            -vf "scale=640:-1" -c:v libwebp -quality 85 \
            -y "$temp_file" 2>/dev/null
        
        if [ -f "$temp_file" ]; then
            # 简单评分: 文件大小 (越大通常内容越丰富)
            local size=$(stat -c%s "$temp_file" 2>/dev/null || echo 0)
            if [ "$size" -gt "$best_score" ]; then
                best_score=$size
                best_time=$time
            fi
            rm -f "$temp_file"
        fi
    done
    
    # 生成最终缩略图
    local final_thumb="$output_dir/$video_id.webp"
    ffmpeg -ss "$best_time" -i "$input_file" -vframes 1 \
        -vf "scale=640:-1" -c:v libwebp -quality 85 \
        -y "$final_thumb" 2>/dev/null
    
    if [ -f "$final_thumb" ]; then
        log "[Thumbnail] 完成: $(du -h "$final_thumb" | cut -f1)"
        echo "$final_thumb"
    else
        log "[Thumbnail] 失败"
        echo ""
    fi
}

# 生成预览视频 (GPU 可选)
generate_preview() {
    local video_id=$1
    local input_file=$2
    local duration=$3
    local output_dir="$PROCESSED_DIR/$video_id/previews"
    mkdir -p "$output_dir"
    
    log "[Preview] 开始生成预览: video_id=$video_id"
    
    local preview_file="$output_dir/$video_id.webm"
    local num_segments=10
    local seg_duration=1
    
    # 短视频调整
    if (( $(echo "$duration < 10" | bc -l) )); then
        num_segments=$(printf "%.0f" "$duration")
        [ "$num_segments" -lt 1 ] && num_segments=1
    fi
    
    # 创建临时文件列表
    local concat_file="$output_dir/concat.txt"
    > "$concat_file"
    
    for i in $(seq 0 $((num_segments - 1))); do
        local position=$(echo "0.05 + 0.9 * $i / ($num_segments - 1)" | bc -l)
        [ "$num_segments" -eq 1 ] && position=0.5
        local start_time=$(echo "$duration * $position" | bc -l)
        local temp_file="$output_dir/seg_$i.webm"
        
        # 使用 GPU 加速解码，CPU 编码 WebM (VP9 没有 NVENC)
        ffmpeg -hwaccel cuda -ss "$start_time" -i "$input_file" \
            -t "$seg_duration" -c:v libvpx-vp9 -b:v 500k \
            -vf "scale=480:-1" -an -y "$temp_file" 2>/dev/null
        
        if [ -f "$temp_file" ]; then
            echo "file '$temp_file'" >> "$concat_file"
        fi
    done
    
    # 拼接
    ffmpeg -f concat -safe 0 -i "$concat_file" \
        -c:v libvpx-vp9 -b:v 500k -y "$preview_file" 2>/dev/null
    
    # 清理临时文件
    rm -f "$output_dir"/seg_*.webm "$concat_file"
    
    if [ -f "$preview_file" ]; then
        log "[Preview] 完成: $(du -h "$preview_file" | cut -f1)"
        echo "$preview_file"
    else
        log "[Preview] 失败"
        echo ""
    fi
}

# HLS 多清晰度转码 (GPU 必须)
transcode_hls() {
    local video_id=$1
    local input_file=$2
    local video_height=$3
    local output_dir="$PROCESSED_DIR/$video_id/hls"
    mkdir -p "$output_dir"
    
    log "[HLS] 开始GPU转码: video_id=$video_id, 源高度=${video_height}p"
    
    # 根据源视频高度决定输出清晰度
    local qualities=""
    if [ "$video_height" -ge 1080 ]; then
        qualities="1080:5000k:192k 720:2500k:128k 480:1000k:96k"
    elif [ "$video_height" -ge 720 ]; then
        qualities="720:2500k:128k 480:1000k:96k"
    else
        qualities="480:1000k:96k"
    fi
    
    local master_content="#EXTM3U\n#EXT-X-VERSION:3\n"
    local success_count=0
    
    for q in $qualities; do
        IFS=':' read -r height vbitrate abitrate <<< "$q"
        local quality_name="${height}p"
        local quality_dir="$output_dir/$quality_name"
        mkdir -p "$quality_dir"
        
        log "[HLS] 转码 $quality_name (GPU NVENC)..."
        
        # NVIDIA NVENC 硬件加速转码
        ffmpeg -hwaccel cuda -hwaccel_output_format cuda \
            -i "$input_file" \
            -c:v h264_nvenc -preset "$GPU_PRESET" -cq "$GPU_CQ" \
            -vf "scale_cuda=-2:$height" \
            -b:v "$vbitrate" -maxrate "$vbitrate" -bufsize "$(echo "$vbitrate" | sed 's/k//')k" \
            -c:a aac -b:a "$abitrate" \
            -hls_time 10 -hls_list_size 0 \
            -hls_segment_filename "$quality_dir/segment_%03d.ts" \
            -y "$quality_dir/playlist.m3u8" 2>/dev/null
        
        if [ -f "$quality_dir/playlist.m3u8" ]; then
            local bandwidth=$((${vbitrate%k} * 1000))
            master_content+="#EXT-X-STREAM-INF:BANDWIDTH=$bandwidth,RESOLUTION=-x$height\n"
            master_content+="$quality_name/playlist.m3u8\n"
            ((success_count++))
            log "[HLS] $quality_name 完成"
        else
            log "[HLS] $quality_name 失败"
        fi
    done
    
    if [ "$success_count" -gt 0 ]; then
        echo -e "$master_content" > "$output_dir/master.m3u8"
        log "[HLS] 转码完成: $success_count 个清晰度"
        echo "$output_dir"
    else
        log "[HLS] 全部失败"
        echo ""
    fi
}

# 同步到主服务器
sync_to_main() {
    local video_id=$1
    local local_dir="$PROCESSED_DIR/$video_id"
    
    log "[Sync] 开始同步到主服务器: video_id=$video_id"
    
    # 同步缩略图
    if [ -d "$local_dir/thumbnails" ]; then
        rsync -avz --progress "$local_dir/thumbnails/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/thumbnails/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # 同步预览
    if [ -d "$local_dir/previews" ]; then
        rsync -avz --progress "$local_dir/previews/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/previews/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # 同步 HLS
    if [ -d "$local_dir/hls" ]; then
        rsync -avz --progress "$local_dir/hls/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/hls/$video_id/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    log "[Sync] 同步完成"
}

# 通知主服务器处理完成
notify_main() {
    local video_id=$1
    local status=$2  # success / failed
    local thumbnail_url=$3
    local preview_url=$4
    local hls_url=$5
    
    log "[Notify] 通知主服务器: video_id=$video_id, status=$status"
    
    # 调用主服务器 API
    curl -s -X POST "http://38.47.218.137:8000/api/v1/admin/transcode-callback" \
        -H "Content-Type: application/json" \
        -H "X-Transcode-Key: YOUR_SECRET_KEY" \
        -d "{
            \"video_id\": $video_id,
            \"status\": \"$status\",
            \"thumbnail_url\": \"$thumbnail_url\",
            \"preview_url\": \"$preview_url\",
            \"hls_url\": \"$hls_url\"
        }" 2>&1 | tee -a "$LOG_FILE"
    
    log "[Notify] 完成"
}

# 处理单个视频
process_video() {
    local video_id=$1
    local input_file=$2
    
    log "========== 开始处理视频: $video_id =========="
    log "输入文件: $input_file"
    
    # 获取视频信息
    local duration=$(ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$input_file" 2>/dev/null)
    local height=$(ffprobe -v error -select_streams v:0 \
        -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$input_file" 2>/dev/null)
    
    duration=${duration:-0}
    height=${height:-720}
    
    log "视频信息: 时长=${duration}s, 高度=${height}p"
    
    # 1. 生成缩略图 (CPU)
    local thumbnail=$(generate_thumbnail "$video_id" "$input_file" "$duration")
    
    # 2. 生成预览 (GPU辅助)
    local preview=$(generate_preview "$video_id" "$input_file" "$duration")
    
    # 3. HLS转码 (GPU)
    local hls_dir=$(transcode_hls "$video_id" "$input_file" "$height")
    
    # 4. 同步到主服务器
    sync_to_main "$video_id"
    
    # 5. 通知主服务器
    local thumb_url="/uploads/thumbnails/$video_id.webp"
    local preview_url="/uploads/previews/$video_id.webm"
    local hls_url="/uploads/hls/$video_id/master.m3u8"
    
    if [ -n "$hls_dir" ]; then
        notify_main "$video_id" "success" "$thumb_url" "$preview_url" "$hls_url"
        log "========== 视频处理成功: $video_id =========="
    else
        notify_main "$video_id" "failed" "" "" ""
        log "========== 视频处理失败: $video_id =========="
    fi
    
    # 清理本地处理文件 (可选)
    # rm -rf "$PROCESSED_DIR/$video_id"
}

# ========== 主程序 ==========
main() {
    mkdir -p "$LOG_DIR"
    
    case "$1" in
        process)
            # 处理单个视频: ./transcode.sh process <video_id> <input_file>
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo "用法: $0 process <video_id> <input_file>"
                exit 1
            fi
            process_video "$2" "$3"
            ;;
        watch)
            # 监控模式: 监控 uploads 目录
            log "启动监控模式..."
            inotifywait -m -e close_write "$UPLOAD_DIR" | while read dir action file; do
                if [[ "$file" =~ \.mp4$ ]] || [[ "$file" =~ \.mov$ ]]; then
                    # 从文件名提取 video_id (假设格式: video_123.mp4)
                    video_id=$(echo "$file" | grep -oP '\d+' | head -1)
                    if [ -n "$video_id" ]; then
                        process_video "$video_id" "$UPLOAD_DIR/$file" &
                    fi
                fi
            done
            ;;
        test)
            # 测试 GPU 编码
            log "测试 GPU 编码..."
            ffmpeg -f lavfi -i testsrc=duration=5:size=1920x1080:rate=30 \
                -c:v h264_nvenc -preset p4 -y /tmp/test_nvenc.mp4 2>&1
            if [ -f /tmp/test_nvenc.mp4 ]; then
                log "GPU 编码测试成功!"
                rm /tmp/test_nvenc.mp4
            else
                log "GPU 编码测试失败!"
            fi
            ;;
        *)
            echo "GPU 视频转码服务"
            echo ""
            echo "用法:"
            echo "  $0 process <video_id> <input_file>  - 处理单个视频"
            echo "  $0 watch                            - 监控模式 (需要 inotify-tools)"
            echo "  $0 test                             - 测试 GPU 编码"
            ;;
    esac
}

main "$@"
