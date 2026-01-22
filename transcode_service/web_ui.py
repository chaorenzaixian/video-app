"""
Transcode Service Web UI v2.0
"""
import os
import json
import shutil
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from config import DIRS, SERVICE, MAIN_SERVER, ensure_dirs, get_free_disk_space
from task_queue import TaskQueue, TaskStatus, TaskType
from transcoder import Transcoder
from uploader import Uploader

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024

queue = TaskQueue()
uploader = Uploader()
pending_publish = {}
upload_progress = {}

# 发布队列 - 确保发布任务串行执行
publish_queue = []
publish_lock = threading.Lock()
publish_worker_running = False


def publish_worker():
    """发布工作线程 - 串行处理发布任务"""
    global publish_worker_running
    while True:
        task_info = None
        with publish_lock:
            if publish_queue:
                task_info = publish_queue.pop(0)
            else:
                publish_worker_running = False
                return
        
        if task_info:
            do_publish_task(task_info)


def do_publish_task(task_info):
    """执行单个发布任务"""
    task_id = task_info['task_id']
    data = task_info['data']
    task_data = task_info['task_data']
    
    try:
        video_id = f"{'short_' if task_data['is_short'] else ''}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 上传HLS文件
        pending_publish[task_id]["publish_progress"] = "上传HLS文件..."
        print(f"[发布] 开始上传HLS: {task_data['hls_dir']} -> {video_id}")
        hls_url = uploader.upload_hls(task_data['hls_dir'], video_id)
        if not hls_url:
            pending_publish[task_id]["status"] = "publish_failed"
            pending_publish[task_id]["publish_error"] = "HLS上传失败"
            return
        print(f"[发布] HLS上传成功: {hls_url}")
        
        # 上传封面
        pending_publish[task_id]["publish_progress"] = "上传封面..."
        print(f"[发布] 开始上传封面: {task_data['covers_dir']}")
        uploader.upload_covers(task_data['covers_dir'], video_id)
        cover_url = f"/uploads/hls/{video_id}/covers/cover_{data.get('selected_cover', task_data['best_cover'])}.webp"
        print(f"[发布] 封面URL: {cover_url}")
        
        # 上传预览视频
        preview_url = ""
        if task_data.get('preview_path'):
            pending_publish[task_id]["publish_progress"] = "上传预览视频..."
            print(f"[发布] 开始上传预览: {task_data['preview_path']}")
            preview_url = uploader.upload_preview(task_data['preview_path']) or ""
            print(f"[发布] 预览URL: {preview_url}")
        
        # 构造视频数据
        pending_publish[task_id]["publish_progress"] = "创建视频记录..."
        import urllib.request
        video_data = {
            "title": data.get('title', task_data['name']),
            "description": data.get('description', ''),
            "hls_url": hls_url, 
            "cover_url": cover_url, 
            "preview_url": preview_url,
            "duration": task_data['duration'], 
            "is_short": task_data['is_short'],
            "is_vip_only": data.get('is_vip_only', False),
            "is_featured": data.get('is_featured', False),
            "coin_price": data.get('coin_price', 0),
            "free_preview_seconds": data.get('free_preview_seconds', 15),
            "status": "PUBLISHED",
        }
        if data.get('category_id'):
            video_data["category_id"] = data['category_id']
        if data.get('tag_ids'):
            video_data["tag_ids"] = data['tag_ids']
        
        print(f"[发布] 调用主服务器API")
        
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/videos/direct-publish",
            data=json.dumps(video_data).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Transcode-Key": MAIN_SERVER['transcode_key']},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
        except urllib.request.HTTPError as e:
            error_body = e.read().decode()
            print(f"[发布] 主服务器返回错误: {e.code} - {error_body}")
            pending_publish[task_id]["status"] = "publish_failed"
            pending_publish[task_id]["publish_error"] = f"主服务器错误: {error_body}"
            return
        
        print(f"[发布] 发布成功: {result}")
        
        queue.add_publish_history(0, task_data['filename'], data.get('title', task_data['name']),
            result.get("id"), task_data['is_short'], task_data['duration'], hls_url, cover_url)
        shutil.rmtree(os.path.join(DIRS["processing"], task_id), ignore_errors=True)
        del pending_publish[task_id]
        
    except Exception as e:
        import traceback
        print(f"[发布] 异常: {traceback.format_exc()}")
        if task_id in pending_publish:
            pending_publish[task_id]["status"] = "publish_failed"
            pending_publish[task_id]["publish_error"] = str(e)


def recover_pending_tasks():
    """Recover pending tasks after service restart"""
    processing_dir = DIRS["processing"]
    if not os.path.exists(processing_dir):
        return
    for task_dir in os.listdir(processing_dir):
        task_path = os.path.join(processing_dir, task_dir)
        if not os.path.isdir(task_path):
            continue
        hls_dir = os.path.join(task_path, "hls")
        covers_dir = os.path.join(task_path, "covers")
        if os.path.exists(hls_dir) and os.path.exists(covers_dir):
            video_files = [f for f in os.listdir(task_path) if f.endswith(('.mp4', '.mov', '.avi', '.mkv')) and not f.endswith('_preview.webm')]
            if not video_files:
                continue
            filename = video_files[0]
            name = os.path.splitext(filename)[0]
            meta_path = os.path.join(task_path, "task_meta.json")
            is_short = False
            is_darkweb = False
            duration = 0
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        is_short = meta.get('is_short', False)
                        is_darkweb = meta.get('is_darkweb', False)
                        duration = meta.get('duration', 0)
                except:
                    pass
            # 如果没有duration，尝试从视频获取
            if duration == 0:
                video_path = os.path.join(task_path, filename)
                try:
                    import subprocess
                    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and result.stdout.strip():
                        duration = float(result.stdout.strip())
                except:
                    pass
            covers = []
            for i in range(1, 11):
                cp = os.path.join(covers_dir, f"cover_{i}.webp")
                if os.path.exists(cp):
                    covers.append({"index": i, "url": f"/api/preview/{task_dir}/covers/cover_{i}.webp", "selected": i == 5})
            preview_path = os.path.join(task_path, f"{name}_preview.webm")
            pending_publish[task_dir] = {
                "status": "ready", "task_id": task_dir, "filename": filename, "name": name,
                "duration": duration, "height": 0, "is_short": is_short, "is_darkweb": is_darkweb,
                "hls_dir": hls_dir, "covers_dir": covers_dir, "covers": covers, "best_cover": 5,
                "preview_path": preview_path if os.path.exists(preview_path) else None,
                "preview_url": f"/api/preview/{task_dir}/{name}_preview.webm" if os.path.exists(preview_path) else None,
                "video_preview_url": f"/api/preview/{task_dir}/hls/master.m3u8"
            }
            print(f"Recovered: {task_dir} - {filename} (short={is_short}, darkweb={is_darkweb})")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/categories')
def get_categories():
    import urllib.request
    darkweb_categories = []
    try:
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/darkweb/transcode/categories",
            headers={"X-Transcode-Key": MAIN_SERVER['transcode_key']}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            darkweb_categories = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Failed to load darkweb categories: {e}")
    try:
        with urllib.request.urlopen(f"{MAIN_SERVER['api_base']}/videos/categories", timeout=10) as resp:
            video_categories = json.loads(resp.read().decode())
        with urllib.request.urlopen(f"{MAIN_SERVER['api_base']}/shorts/categories", timeout=10) as resp:
            short_categories = json.loads(resp.read().decode())
        return jsonify({
            "video_categories": video_categories if isinstance(video_categories, list) else [],
            "short_categories": short_categories if isinstance(short_categories, list) else [],
            "darkweb_categories": darkweb_categories
        })
    except Exception as e:
        print(f"Failed to load categories: {e}")
        return jsonify({"video_categories": [], "short_categories": [], "darkweb_categories": darkweb_categories})


@app.route('/api/tags')
def get_tags():
    import urllib.request
    darkweb_tags = []
    try:
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/darkweb/transcode/tags",
            headers={"X-Transcode-Key": MAIN_SERVER['transcode_key']}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            darkweb_tags = data.get('items', []) if isinstance(data, dict) else data
    except Exception as e:
        print(f"Failed to load darkweb tags: {e}")
    try:
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/videos/transcode/tags",
            headers={"X-Transcode-Key": MAIN_SERVER['transcode_key']},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            tags = result.get("items", [])
        return jsonify({
            "tags": [{"id": t.get("id"), "name": t.get("name")} for t in tags],
            "darkweb_tags": darkweb_tags
        })
    except Exception as e:
        print(f"Failed to load tags: {e}")
        return jsonify({"tags": [], "darkweb_tags": darkweb_tags})


@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400
    files = request.files.getlist('video')
    video_type = request.form.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb'
    results = []
    for file in files:
        if not file.filename:
            continue
        task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        task_dir = os.path.join(DIRS["processing"], task_id)
        os.makedirs(task_dir, exist_ok=True)
        video_path = os.path.join(task_dir, file.filename)
        file.save(video_path)
        pending_publish[task_id] = {"status": "uploading", "progress": 0, "filename": file.filename}
        def transcode(tid, vpath, short, darkweb):
            try:
                result = process_video(tid, vpath, short, darkweb)
                pending_publish[tid] = result
            except Exception as e:
                pending_publish[tid] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()
        results.append({"task_id": task_id, "filename": file.filename})
    return jsonify({"tasks": results, "count": len(results)})


@app.route('/api/add-local', methods=['POST'])
def add_local_file():
    data = request.json
    # 支持单个路径或多个路径
    paths = data.get('paths', [])
    local_path = data.get('path', '').strip()
    if local_path and not paths:
        paths = [local_path]
    
    video_type = data.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb'
    
    if not paths:
        return jsonify({"error": "Path is required"}), 400
    
    results = []
    errors = []
    
    for local_path in paths:
        local_path = local_path.strip()
        if not local_path:
            continue
            
        if not os.path.exists(local_path):
            errors.append({"path": local_path, "error": "File not found"})
            continue
        if not os.path.isfile(local_path):
            errors.append({"path": local_path, "error": "Not a file"})
            continue
        ext = os.path.splitext(local_path)[1].lower()
        if ext not in ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'):
            errors.append({"path": local_path, "error": f"Unsupported format: {ext}"})
            continue
        
        task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        task_dir = os.path.join(DIRS["processing"], task_id)
        os.makedirs(task_dir, exist_ok=True)
        filename = os.path.basename(local_path)
        video_path = os.path.join(task_dir, filename)
        
        try:
            # 优先尝试硬链接（同磁盘瞬间完成）
            try:
                os.link(local_path, video_path)
                print(f"Hard link created: {local_path} -> {video_path}")
            except (OSError, AttributeError):
                # 硬链接失败（跨磁盘或不支持），使用复制
                shutil.copy2(local_path, video_path)
                print(f"File copied: {local_path} -> {video_path}")
        except Exception as e:
            errors.append({"path": local_path, "error": f"Copy failed: {str(e)}"})
            continue
        
        pending_publish[task_id] = {"status": "uploading", "progress": 0, "filename": filename}
        
        def transcode(tid, vpath, short, darkweb):
            try:
                result = process_video(tid, vpath, short, darkweb)
                pending_publish[tid] = result
            except Exception as e:
                pending_publish[tid] = {"error": str(e), "status": "failed"}
        
        threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()
        results.append({"task_id": task_id, "filename": filename, "path": local_path})
    
    return jsonify({
        "success": len(results) > 0,
        "tasks": results,
        "count": len(results),
        "errors": errors,
        "error_count": len(errors)
    })


@app.route('/api/upload/chunk', methods=['POST'])
def upload_chunk():
    file_id = request.form.get('file_id')
    chunk_index = int(request.form.get('chunk_index', 0))
    total_chunks = int(request.form.get('total_chunks', 1))
    filename = request.form.get('filename')
    video_type = request.form.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb'
    if 'chunk' not in request.files:
        return jsonify({"error": "No chunk data"}), 400
    temp_dir = os.path.join(DIRS["uploads"], file_id)
    os.makedirs(temp_dir, exist_ok=True)
    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index}")
    request.files['chunk'].save(chunk_path)
    upload_progress[file_id] = {"progress": (chunk_index + 1) / total_chunks * 100}
    if chunk_index + 1 == total_chunks:
        task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        task_dir = os.path.join(DIRS["processing"], task_id)
        os.makedirs(task_dir, exist_ok=True)
        video_path = os.path.join(task_dir, filename)
        with open(video_path, 'wb') as outfile:
            for i in range(total_chunks):
                with open(os.path.join(temp_dir, f"chunk_{i}"), 'rb') as infile:
                    outfile.write(infile.read())
        shutil.rmtree(temp_dir, ignore_errors=True)
        del upload_progress[file_id]
        pending_publish[task_id] = {"status": "uploading", "progress": 0, "filename": filename}
        def transcode():
            try:
                result = process_video(task_id, video_path, is_short, is_darkweb)
                pending_publish[task_id] = result
            except Exception as e:
                pending_publish[task_id] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode).start()
        return jsonify({"complete": True, "task_id": task_id})
    return jsonify({"complete": False, "progress": upload_progress[file_id]["progress"]})


def process_video(task_id, video_path, is_short, is_darkweb=False):
    task_dir = os.path.dirname(video_path)
    filename = os.path.basename(video_path)
    name = os.path.splitext(filename)[0]
    def progress_cb(p):
        pending_publish[task_id] = {"status": "processing", "progress": p, "filename": filename}
    transcoder = Transcoder(progress_cb, is_short=is_short)
    duration, height = transcoder.get_video_info(video_path)
    pending_publish[task_id] = {"status": "transcoding", "progress": 0, "filename": filename}
    hls_dir = transcoder.generate_hls(video_path, task_dir, duration, height)
    pending_publish[task_id] = {"status": "generating_covers", "progress": 100, "filename": filename}
    covers_dir, best_cover = transcoder.generate_covers(video_path, task_dir, duration)
    preview_path = None
    if not is_short:
        preview_path = transcoder.generate_preview(video_path, task_dir, duration, name)
    covers = []
    for i in range(1, 11):
        cp = os.path.join(covers_dir, f"cover_{i}.webp")
        if os.path.exists(cp):
            covers.append({"index": i, "url": f"/api/preview/{task_id}/covers/cover_{i}.webp", "selected": i == best_cover})
    meta_path = os.path.join(task_dir, "task_meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({"is_short": is_short, "is_darkweb": is_darkweb, "duration": duration, "filename": filename}, f)
    return {
        "status": "ready", "task_id": task_id, "filename": filename, "name": name,
        "duration": duration, "height": height, "is_short": is_short, "is_darkweb": is_darkweb,
        "hls_dir": hls_dir, "covers_dir": covers_dir, "covers": covers, "best_cover": best_cover,
        "preview_path": preview_path,
        "preview_url": f"/api/preview/{task_id}/{name}_preview.webm" if preview_path else None,
        "video_preview_url": f"/api/preview/{task_id}/hls/master.m3u8"
    }


@app.route('/api/status/<task_id>')
def get_task_status(task_id):
    if task_id in pending_publish:
        return jsonify(pending_publish[task_id])
    return jsonify({"status": "not_found"}), 404


@app.route('/api/preview/<task_id>/<path:filepath>')
def serve_preview(task_id, filepath):
    return send_from_directory(os.path.join(DIRS["processing"], task_id), filepath)


@app.route('/api/upload-cover', methods=['POST'])
def upload_cover():
    if 'cover' not in request.files:
        return jsonify({"error": "No cover file"}), 400
    task_id = request.form.get('task_id')
    if not task_id:
        return jsonify({"error": "No task_id"}), 400
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    cover_file = request.files['cover']
    if not cover_file.filename:
        return jsonify({"error": "Empty filename"}), 400
    task_dir = os.path.join(DIRS["processing"], task_id)
    covers_dir = os.path.join(task_dir, "covers")
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)
    import subprocess
    temp_path = os.path.join(covers_dir, "temp_upload" + os.path.splitext(cover_file.filename)[1])
    cover_file.save(temp_path)
    output_path = os.path.join(covers_dir, "custom_cover.webp")
    try:
        cmd = ["ffmpeg", "-y", "-i", temp_path, "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2", "-q:v", "85", output_path]
        subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(output_path):
            return jsonify({"success": True, "url": f"/api/preview/{task_id}/covers/custom_cover.webp"})
        else:
            return jsonify({"error": "Failed to convert image"}), 500
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500


@app.route('/api/schedule', methods=['POST'])
def schedule_publish():
    data = request.json
    task_id = data.get('task_id')
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    pending_publish[task_id]["scheduled_at"] = data.get('scheduled_time')
    pending_publish[task_id]["status"] = "scheduled"
    return jsonify({"success": True})


@app.route('/api/publish', methods=['POST'])
def publish_video():
    global publish_worker_running
    
    data = request.json
    task_id = data.get('task_id')
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    task_data = pending_publish[task_id]
    if task_data.get("status") not in ("ready", "scheduled"):
        return jsonify({"error": "Video not ready"}), 400
    
    # 标记为正在发布
    pending_publish[task_id]["status"] = "publishing"
    pending_publish[task_id]["publish_progress"] = "排队中..."
    
    # 添加到发布队列
    task_info = {
        'task_id': task_id,
        'data': data.copy(),
        'task_data': task_data.copy()
    }
    
    with publish_lock:
        publish_queue.append(task_info)
        queue_pos = len(publish_queue)
        pending_publish[task_id]["publish_progress"] = f"排队中 (第{queue_pos}位)..."
        
        # 如果工作线程没有运行，启动它
        if not publish_worker_running:
            publish_worker_running = True
            threading.Thread(target=publish_worker, daemon=True).start()
    
    return jsonify({"success": True, "message": "发布任务已加入队列", "task_id": task_id, "queue_position": queue_pos})


@app.route('/api/publish-darkweb', methods=['POST'])
def publish_darkweb_video():
    data = request.json
    task_id = data.get('task_id')
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    task_data = pending_publish[task_id]
    if task_data.get("status") not in ("ready", "scheduled"):
        return jsonify({"error": "Video not ready"}), 400
    try:
        video_id = f"darkweb_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        hls_url = uploader.upload_darkweb_hls(task_data['hls_dir'], video_id)
        uploader.upload_darkweb_covers(task_data['covers_dir'], video_id)
        cover_url = f"/uploads/darkweb_hls/{video_id}/covers/cover_{data.get('selected_cover', task_data['best_cover'])}.webp"
        preview_url = ""
        if task_data.get('preview_path'):
            preview_url = uploader.upload_darkweb_preview(task_data['preview_path'], video_id) or ""
        import urllib.request
        video_data = {
            "title": data.get('title', task_data['name']),
            "description": data.get('description', ''),
            "hls_url": hls_url, "cover_url": cover_url, "preview_url": preview_url,
            "duration": task_data['duration'],
            "is_featured": data.get('is_featured', False),
        }
        if data.get('category_id'):
            video_data["category_id"] = data['category_id']
        if data.get('tag_ids'):
            video_data["tags"] = data['tag_ids']
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/darkweb/transcode/videos",
            data=json.dumps(video_data).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Transcode-Key": MAIN_SERVER['transcode_key']},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        queue.add_publish_history(0, task_data['filename'], data.get('title', task_data['name']),
            result.get("id"), False, task_data['duration'], hls_url, cover_url, is_darkweb=True)
        shutil.rmtree(os.path.join(DIRS["processing"], task_id), ignore_errors=True)
        del pending_publish[task_id]
        return jsonify({"success": True, "video_id": result.get("id")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reorder', methods=['POST'])
def reorder_pending():
    data = request.json
    order = data.get('order', [])
    if not order:
        return jsonify({"error": "No order provided"}), 400
    return jsonify({"success": True})


@app.route('/api/tasks')
def get_tasks():
    tasks = queue.get_recent_tasks(limit=50)
    return jsonify(tasks)


@app.route('/api/queue')
def get_queue():
    """返回正在处理的任务（转码中或发布中）"""
    result = []
    for task_id, data in pending_publish.items():
        status = data.get("status", "")
        # 正在处理的任务：uploading, processing, transcoding, generating_covers, publishing, publish_failed
        if status not in ("ready", "scheduled"):
            item = {"task_id": task_id, **data}
            result.append(item)
    return jsonify(result)


@app.route('/api/pending')
def get_pending():
    """返回待发布的任务（状态是ready/scheduled的）"""
    result = []
    for task_id, data in pending_publish.items():
        status = data.get("status", "")
        # 待发布的任务：ready, scheduled（不包括publishing和publish_failed）
        if status in ("ready", "scheduled"):
            item = {"task_id": task_id, **data}
            result.append(item)
    return jsonify(result)


@app.route('/api/set-type/<task_id>', methods=['POST'])
def set_video_type(task_id):
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    data = request.json
    video_type = data.get('video_type', 'long')
    pending_publish[task_id]['is_short'] = video_type == 'short'
    pending_publish[task_id]['is_darkweb'] = video_type == 'darkweb'
    task_dir = os.path.join(DIRS["processing"], task_id)
    meta_path = os.path.join(task_dir, "task_meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            meta['is_short'] = video_type == 'short'
            meta['is_darkweb'] = video_type == 'darkweb'
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f)
        except:
            pass
    return jsonify({"success": True})


@app.route('/api/delete/<task_id>', methods=['DELETE', 'POST'])
def delete_task(task_id):
    if task_id in pending_publish:
        task_dir = os.path.join(DIRS["processing"], task_id)
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)
        del pending_publish[task_id]
        return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404


@app.route('/api/delete-batch', methods=['POST'])
def delete_batch():
    """批量删除待发布任务"""
    data = request.json
    task_ids = data.get('task_ids', [])
    if not task_ids:
        return jsonify({"error": "No task_ids provided"}), 400
    
    deleted = []
    failed = []
    for task_id in task_ids:
        if task_id in pending_publish:
            task_dir = os.path.join(DIRS["processing"], task_id)
            if os.path.exists(task_dir):
                try:
                    shutil.rmtree(task_dir, ignore_errors=True)
                except Exception as e:
                    failed.append({"task_id": task_id, "error": str(e)})
                    continue
            del pending_publish[task_id]
            deleted.append(task_id)
        else:
            failed.append({"task_id": task_id, "error": "Task not found"})
    
    return jsonify({
        "success": True,
        "deleted": deleted,
        "deleted_count": len(deleted),
        "failed": failed,
        "failed_count": len(failed)
    })


@app.route('/api/history')
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    items = queue.get_publish_history(limit=per_page, offset=offset)
    stats = queue.get_history_stats()
    return jsonify({
        "items": items,
        "stats": stats,
        "page": page,
        "per_page": per_page
    })


@app.route('/api/browse')
def browse_directory():
    """浏览服务器目录"""
    path = request.args.get('path', '')
    
    # 默认目录列表
    default_dirs = [
        {"name": "D:\\", "path": "D:\\", "type": "drive"},
        {"name": "E:\\", "path": "E:\\", "type": "drive"},
        {"name": "C:\\", "path": "C:\\", "type": "drive"},
    ]
    
    if not path:
        # 返回默认驱动器列表
        return jsonify({"items": default_dirs, "current": "", "parent": ""})
    
    # 规范化路径
    path = os.path.normpath(path)
    
    if not os.path.exists(path):
        return jsonify({"error": "Path not found"}), 404
    
    if not os.path.isdir(path):
        return jsonify({"error": "Not a directory"}), 400
    
    items = []
    try:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            try:
                is_dir = os.path.isdir(full_path)
                # 只显示目录和视频文件
                if is_dir:
                    items.append({"name": name, "path": full_path, "type": "folder"})
                else:
                    ext = os.path.splitext(name)[1].lower()
                    if ext in ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'):
                        size = os.path.getsize(full_path)
                        items.append({"name": name, "path": full_path, "type": "video", "size": size})
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError) as e:
        return jsonify({"error": str(e)}), 403
    
    # 排序：文件夹在前，然后按名称排序
    items.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
    
    # 计算父目录
    parent = os.path.dirname(path)
    if parent == path:  # 根目录
        parent = ""
    
    return jsonify({"items": items, "current": path, "parent": parent})


@app.route('/api/system')
def get_system_info():
    import shutil
    try:
        total, used, free = shutil.disk_usage(DIRS["processing"])
        disk_free_gb = round(free / (1024 ** 3), 2)
        disk_total_gb = round(total / (1024 ** 3), 2)
        disk_used_percent = round(used / total * 100, 1) if total > 0 else 0
    except:
        disk_free_gb = 0
        disk_total_gb = 0
        disk_used_percent = 0
    
    processing_count = len([d for d in os.listdir(DIRS["processing"]) if os.path.isdir(os.path.join(DIRS["processing"], d))]) if os.path.exists(DIRS["processing"]) else 0
    return jsonify({
        "disk_free_gb": disk_free_gb,
        "disk_total_gb": disk_total_gb,
        "disk_used_percent": disk_used_percent,
        "processing_count": processing_count,
        "pending_count": len(pending_publish),
        "queue_count": len([t for t in pending_publish.values() if t.get("status") not in ("ready", "scheduled", "publishing", "publish_failed")]),
        "service_version": "2.0"
    })


def run_web_ui(host='0.0.0.0', port=8080):
    ensure_dirs()
    recover_pending_tasks()
    print(f"Web UI starting on http://{host}:{port}")
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    run_web_ui()
