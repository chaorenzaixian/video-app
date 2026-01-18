#!/bin/bash
# GPU Video Watch Service
# Monitors uploads directory and auto-processes new videos
# Deploy to: GPU Server ~/video-transcode/watch_service.sh

WORK_DIR="$HOME/video-transcode"
UPLOAD_DIR="$WORK_DIR/uploads"
LOG_DIR="$WORK_DIR/logs"
PID_FILE="$WORK_DIR/watch.pid"
LOG_FILE="$LOG_DIR/watch_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

start_watch() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Watch service already running (PID: $pid)"
            exit 1
        fi
    fi
    
    mkdir -p "$LOG_DIR" "$UPLOAD_DIR"
    
    log "Starting watch service..."
    log "Monitoring: $UPLOAD_DIR"
    
    # Check inotifywait
    if ! command -v inotifywait &> /dev/null; then
        log "ERROR: inotifywait not found. Install: sudo apt install inotify-tools"
        exit 1
    fi
    
    # Start monitoring in background
    (
        inotifywait -m -e close_write -e moved_to "$UPLOAD_DIR" --format '%f' 2>/dev/null | while read filename; do
            # Check video file extension
            ext="${filename##*.}"
            ext_lower=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
            
            if [[ "$ext_lower" =~ ^(mp4|mov|avi|mkv|webm)$ ]]; then
                log "New video detected: $filename"
                
                # Extract video_id from filename (format: {video_id}_{uuid}.mp4)
                video_id=$(echo "$filename" | grep -oP '^\d+' | head -1)
                
                if [ -n "$video_id" ]; then
                    input_file="$UPLOAD_DIR/$filename"
                    
                    # Wait for file to be fully written
                    sleep 2
                    
                    # Check file size is stable
                    local size1=$(stat -c%s "$input_file" 2>/dev/null || echo 0)
                    sleep 1
                    local size2=$(stat -c%s "$input_file" 2>/dev/null || echo 0)
                    
                    if [ "$size1" = "$size2" ] && [ "$size1" -gt 0 ]; then
                        log "Processing video: id=$video_id, file=$filename"
                        
                        # Run transcode in background
                        nohup "$WORK_DIR/transcode.sh" process "$video_id" "$input_file" \
                            >> "$LOG_DIR/video_$video_id.log" 2>&1 &
                        
                        log "Transcode job started for video $video_id (PID: $!)"
                    else
                        log "File still being written, skipping: $filename"
                    fi
                else
                    log "Cannot extract video_id from filename: $filename"
                fi
            fi
        done
    ) &
    
    local watch_pid=$!
    echo $watch_pid > "$PID_FILE"
    
    log "Watch service started (PID: $watch_pid)"
    echo "Watch service started (PID: $watch_pid)"
}

stop_watch() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping watch service (PID: $pid)..."
            kill "$pid" 2>/dev/null
            
            # Also kill inotifywait processes
            pkill -f "inotifywait.*$UPLOAD_DIR" 2>/dev/null
            
            rm -f "$PID_FILE"
            log "Watch service stopped"
            echo "Watch service stopped"
        else
            echo "Watch service not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "Watch service not running"
    fi
}

status_watch() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Watch service is running (PID: $pid)"
            
            # Show recent activity
            echo ""
            echo "Recent activity (last 10 lines):"
            tail -10 "$LOG_FILE" 2>/dev/null || echo "No logs yet"
            
            # Show current processing
            echo ""
            echo "Currently processing:"
            ps aux | grep "transcode.sh process" | grep -v grep || echo "None"
        else
            echo "Watch service not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "Watch service not running"
    fi
}

case "$1" in
    start)
        start_watch
        ;;
    stop)
        stop_watch
        ;;
    restart)
        stop_watch
        sleep 2
        start_watch
        ;;
    status)
        status_watch
        ;;
    *)
        echo "GPU Video Watch Service"
        echo ""
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start monitoring uploads directory"
        echo "  stop    - Stop the watch service"
        echo "  restart - Restart the watch service"
        echo "  status  - Show service status and recent activity"
        ;;
esac
