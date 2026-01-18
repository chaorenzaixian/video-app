#!/bin/bash
# GPU Video Transcoding Script
# Deploy to: GPU Server ~/video-transcode/transcode.sh

set -e

# ========== Configuration ==========
WORK_DIR="$HOME/video-transcode"
UPLOAD_DIR="$WORK_DIR/uploads"
PROCESSED_DIR="$WORK_DIR/processed"
LOG_DIR="$WORK_DIR/logs"
LOG_FILE="$LOG_DIR/transcode_$(date +%Y%m%d).log"

# Main server config
MAIN_SERVER="root@38.47.218.137"
MAIN_PROJECT="/www/wwwroot/video-app"
MAIN_UPLOAD_DIR="$MAIN_PROJECT/backend/uploads"

# GPU encoding params
GPU_PRESET="p4"
GPU_CQ="23"

# ========== Functions ==========
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

generate_thumbnail() {
    local video_id=$1
    local input_file=$2
    local duration=$3
    local output_dir="$PROCESSED_DIR/$video_id/thumbnails"
    mkdir -p "$output_dir"
    
    log "[Thumbnail] Starting: video_id=$video_id"
    
    local best_score=0
    local best_time=1
    
    for pct in 10 25 40 55 70; do
        local time_val=$(echo "scale=2; $duration * $pct / 100" | bc)
        local temp_file="$output_dir/temp_$pct.webp"
        
        ffmpeg -ss "$time_val" -i "$input_file" -vframes 1 \
            -vf "scale=640:-1" -c:v libwebp -quality 85 \
            -y "$temp_file" 2>/dev/null || true
        
        if [ -f "$temp_file" ]; then
            local size=$(stat -c%s "$temp_file" 2>/dev/null || echo 0)
            if [ "$size" -gt "$best_score" ]; then
                best_score=$size
                best_time=$time_val
            fi
            rm -f "$temp_file"
        fi
    done
    
    local final_thumb="$output_dir/$video_id.webp"
    ffmpeg -ss "$best_time" -i "$input_file" -vframes 1 \
        -vf "scale=640:-1" -c:v libwebp -quality 85 \
        -y "$final_thumb" 2>/dev/null || true
    
    if [ -f "$final_thumb" ]; then
        log "[Thumbnail] Done: $(du -h "$final_thumb" | cut -f1)"
        echo "$final_thumb"
    else
        log "[Thumbnail] Failed"
        echo ""
    fi
}

generate_preview() {
    local video_id=$1
    local input_file=$2
    local duration=$3
    local output_dir="$PROCESSED_DIR/$video_id/previews"
    mkdir -p "$output_dir"
    
    log "[Preview] Starting: video_id=$video_id"
    
    local preview_file="$output_dir/$video_id.webm"
    local num_segments=10
    local seg_duration=1
    
    local is_short=$(echo "$duration < 10" | bc -l)
    if [ "$is_short" = "1" ]; then
        num_segments=$(printf "%.0f" "$duration")
        if [ "$num_segments" -lt 1 ]; then
            num_segments=1
        fi
    fi
    
    local concat_file="$output_dir/concat.txt"
    rm -f "$concat_file"
    touch "$concat_file"
    
    for i in $(seq 0 $((num_segments - 1))); do
        local position
        if [ "$num_segments" -eq 1 ]; then
            position="0.5"
        else
            position=$(echo "scale=4; 0.05 + 0.9 * $i / ($num_segments - 1)" | bc)
        fi
        local start_time=$(echo "scale=2; $duration * $position" | bc)
        local temp_file="$output_dir/seg_$i.webm"
        
        ffmpeg -hwaccel cuda -ss "$start_time" -i "$input_file" \
            -t "$seg_duration" -c:v libvpx-vp9 -b:v 500k \
            -vf "scale=480:-1" -an -y "$temp_file" 2>/dev/null || true
        
        if [ -f "$temp_file" ]; then
            echo "file '$temp_file'" >> "$concat_file"
        fi
    done
    
    ffmpeg -f concat -safe 0 -i "$concat_file" \
        -c:v libvpx-vp9 -b:v 500k -y "$preview_file" 2>/dev/null || true
    
    rm -f "$output_dir"/seg_*.webm "$concat_file"
    
    if [ -f "$preview_file" ]; then
        log "[Preview] Done: $(du -h "$preview_file" | cut -f1)"
        echo "$preview_file"
    else
        log "[Preview] Failed"
        echo ""
    fi
}

transcode_hls() {
    local video_id=$1
    local input_file=$2
    local video_height=$3
    local output_dir="$PROCESSED_DIR/$video_id/hls"
    mkdir -p "$output_dir"
    
    log "[HLS] Starting GPU transcode: video_id=$video_id, height=${video_height}p"
    
    local qualities=""
    if [ "$video_height" -ge 1080 ]; then
        qualities="1080:5000k:192k 720:2500k:128k 480:1000k:96k"
    elif [ "$video_height" -ge 720 ]; then
        qualities="720:2500k:128k 480:1000k:96k"
    else
        qualities="480:1000k:96k"
    fi
    
    local master_content="#EXTM3U
#EXT-X-VERSION:3
"
    local success_count=0
    
    for q in $qualities; do
        local height=$(echo "$q" | cut -d: -f1)
        local vbitrate=$(echo "$q" | cut -d: -f2)
        local abitrate=$(echo "$q" | cut -d: -f3)
        local quality_name="${height}p"
        local quality_dir="$output_dir/$quality_name"
        mkdir -p "$quality_dir"
        
        log "[HLS] Transcoding $quality_name (GPU NVENC)..."
        
        ffmpeg -hwaccel cuda -hwaccel_output_format cuda \
            -i "$input_file" \
            -c:v h264_nvenc -preset "$GPU_PRESET" -cq "$GPU_CQ" \
            -vf "scale_cuda=-2:$height" \
            -b:v "$vbitrate" -maxrate "$vbitrate" -bufsize "${vbitrate%k}k" \
            -c:a aac -b:a "$abitrate" \
            -hls_time 10 -hls_list_size 0 \
            -hls_segment_filename "$quality_dir/segment_%03d.ts" \
            -y "$quality_dir/playlist.m3u8" 2>/dev/null || true
        
        if [ -f "$quality_dir/playlist.m3u8" ]; then
            local bandwidth=$((${vbitrate%k} * 1000))
            master_content+="#EXT-X-STREAM-INF:BANDWIDTH=$bandwidth,RESOLUTION=-x$height
$quality_name/playlist.m3u8
"
            success_count=$((success_count + 1))
            log "[HLS] $quality_name done"
        else
            log "[HLS] $quality_name failed"
        fi
    done
    
    if [ "$success_count" -gt 0 ]; then
        echo "$master_content" > "$output_dir/master.m3u8"
        log "[HLS] Transcode complete: $success_count qualities"
        echo "$output_dir"
    else
        log "[HLS] All failed"
        echo ""
    fi
}

sync_to_main() {
    local video_id=$1
    local local_dir="$PROCESSED_DIR/$video_id"
    
    log "[Sync] Syncing to main server: video_id=$video_id"
    
    if [ -d "$local_dir/thumbnails" ]; then
        rsync -avz "$local_dir/thumbnails/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/thumbnails/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    if [ -d "$local_dir/previews" ]; then
        rsync -avz "$local_dir/previews/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/previews/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    if [ -d "$local_dir/hls" ]; then
        rsync -avz "$local_dir/hls/" \
            "$MAIN_SERVER:$MAIN_UPLOAD_DIR/hls/$video_id/" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    log "[Sync] Done"
}

notify_main() {
    local video_id=$1
    local status=$2
    local thumbnail_url=$3
    local preview_url=$4
    local hls_url=$5
    
    log "[Notify] Notifying main server: video_id=$video_id, status=$status"
    
    curl -s -X POST "http://38.47.218.137:8000/api/v1/admin/transcode-callback" \
        -H "Content-Type: application/json" \
        -H "X-Transcode-Key: vYTWoms4FKOqySca1jCLtNHRVz3BAI6U" \
        -d "{
            \"video_id\": $video_id,
            \"status\": \"$status\",
            \"thumbnail_url\": \"$thumbnail_url\",
            \"preview_url\": \"$preview_url\",
            \"hls_url\": \"$hls_url\"
        }" 2>&1 | tee -a "$LOG_FILE"
    
    log "[Notify] Done"
}

process_video() {
    local video_id=$1
    local input_file=$2
    
    log "========== Processing video: $video_id =========="
    log "Input: $input_file"
    
    local duration=$(ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$input_file" 2>/dev/null || echo "0")
    local height=$(ffprobe -v error -select_streams v:0 \
        -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$input_file" 2>/dev/null || echo "720")
    
    duration=${duration:-0}
    height=${height:-720}
    
    log "Video info: duration=${duration}s, height=${height}p"
    
    local thumbnail=$(generate_thumbnail "$video_id" "$input_file" "$duration")
    local preview=$(generate_preview "$video_id" "$input_file" "$duration")
    local hls_dir=$(transcode_hls "$video_id" "$input_file" "$height")
    
    sync_to_main "$video_id"
    
    local thumb_url="/uploads/thumbnails/$video_id.webp"
    local preview_url="/uploads/previews/$video_id.webm"
    local hls_url="/uploads/hls/$video_id/master.m3u8"
    
    if [ -n "$hls_dir" ]; then
        notify_main "$video_id" "success" "$thumb_url" "$preview_url" "$hls_url"
        log "========== Video processed successfully: $video_id =========="
    else
        notify_main "$video_id" "failed" "" "" ""
        log "========== Video processing failed: $video_id =========="
    fi
}

# ========== Main ==========
main() {
    mkdir -p "$LOG_DIR"
    
    case "$1" in
        process)
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo "Usage: $0 process <video_id> <input_file>"
                exit 1
            fi
            process_video "$2" "$3"
            ;;
        test)
            log "Testing GPU encoding..."
            ffmpeg -f lavfi -i testsrc=duration=5:size=1920x1080:rate=30 \
                -c:v h264_nvenc -preset p4 -y /tmp/test_nvenc.mp4 2>&1
            if [ -f /tmp/test_nvenc.mp4 ]; then
                log "GPU encoding test SUCCESS!"
                rm /tmp/test_nvenc.mp4
            else
                log "GPU encoding test FAILED!"
            fi
            ;;
        *)
            echo "GPU Video Transcoding Service"
            echo ""
            echo "Usage:"
            echo "  $0 process <video_id> <input_file>  - Process a video"
            echo "  $0 test                             - Test GPU encoding"
            ;;
    esac
}

main "$@"
