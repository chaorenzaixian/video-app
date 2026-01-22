"""
创建web_ui.py文件
"""
import os

content = '''"""
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
            # Read metadata file if exists
            meta_path = os.path.join(task_path, "task_meta.json")
            is_short = False
            duration = 0
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        is_short = meta.get('is_short', False)
                        duration = meta.get('duration', 0)
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
                "duration": duration, "height": 0, "is_short": is_short,
                "hls_dir": hls_dir, "covers_dir": covers_dir, "covers": covers, "best_cover": 5,
                "preview_path": preview_path if os.path.exists(preview_path) else None,
                "preview_url": f"/api/preview/{task_dir}/{name}_preview.webm" if os.path.exists(preview_path) else None,
                "video_preview_url": f"/api/preview/{task_dir}/hls/master.m3u8"
            }
            print(f"Recovered: {task_dir} - {filename} (short={is_short})")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/categories')
def get_categories():
    import urllib.request
    try:
        with urllib.request.urlopen(f"{MAIN_SERVER['api_base']}/videos/categories/by-type?category_type=video", timeout=10) as resp:
            video_categories = json.loads(resp.read().decode())
        with urllib.request.urlopen(f"{MAIN_SERVER['api_base']}/videos/categories/by-type?category_type=short", timeout=10) as resp:
            short_categories = json.loads(resp.read().decode())
        return jsonify({"categories": video_categories or [], "short_categories": short_categories or []})
    except:
        return jsonify({"categories": [], "short_categories": []})


@app.route('/api/tags')
def get_tags():
    import urllib.request
    try:
        with urllib.request.urlopen(f"{MAIN_SERVER['api_base']}/tags?limit=100", timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return jsonify({"tags": data.get("items", [])})
    except:
        return jsonify({"tags": []})


@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file"}), 400
    files = request.files.getlist('video')
    is_short = request.form.get('is_short', 'false') == 'true'
    results = []
    for file in files:
        if not file.filename:
            continue
        task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        task_dir = os.path.join(DIRS["processing"], task_id)
        os.makedirs(task_dir, exist_ok=True)
        video_path = os.path.join(task_dir, file.filename)
        file.save(video_path)
        def transcode(tid, vpath, short):
            try:
                result = process_video(tid, vpath, short)
                pending_publish[tid] = result
            except Exception as e:
                pending_publish[tid] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode, args=(task_id, video_path, is_short)).start()
        results.append({"task_id": task_id, "filename": file.filename})
    return jsonify({"tasks": results, "count": len(results)})


@app.route('/api/add-local', methods=['POST'])
def add_local_file():
    """Add local file to transcode queue (instant, no upload needed)"""
    data = request.json
    local_path = data.get('path', '').strip()
    is_short = data.get('is_short', False)
    if not local_path:
        return jsonify({"error": "Path is required"}), 400
    if not os.path.exists(local_path):
        return jsonify({"error": f"File not found: {local_path}"}), 404
    if not os.path.isfile(local_path):
        return jsonify({"error": "Path is not a file"}), 400
    ext = os.path.splitext(local_path)[1].lower()
    if ext not in ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'):
        return jsonify({"error": f"Unsupported format: {ext}"}), 400
    task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    task_dir = os.path.join(DIRS["processing"], task_id)
    os.makedirs(task_dir, exist_ok=True)
    filename = os.path.basename(local_path)
    video_path = os.path.join(task_dir, filename)
    try:
        shutil.copy2(local_path, video_path)
    except Exception as e:
        return jsonify({"error": f"Copy failed: {str(e)}"}), 500
    def transcode(tid, vpath, short):
        try:
            result = process_video(tid, vpath, short)
            pending_publish[tid] = result
        except Exception as e:
            pending_publish[tid] = {"error": str(e), "status": "failed"}
    threading.Thread(target=transcode, args=(task_id, video_path, is_short)).start()
    return jsonify({"success": True, "task_id": task_id, "filename": filename})


@app.route('/api/upload/chunk', methods=['POST'])
def upload_chunk():
    file_id = request.form.get('file_id')
    chunk_index = int(request.form.get('chunk_index', 0))
    total_chunks = int(request.form.get('total_chunks', 1))
    filename = request.form.get('filename')
    is_short = request.form.get('is_short', 'false') == 'true'
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
        def transcode():
            try:
                result = process_video(task_id, video_path, is_short)
                pending_publish[task_id] = result
            except Exception as e:
                pending_publish[task_id] = {"error": str(e), "status": "failed"}
        threading.Thread(target=transcode).start()
        return jsonify({"complete": True, "task_id": task_id})
    return jsonify({"complete": False, "progress": upload_progress[file_id]["progress"]})


def process_video(task_id, video_path, is_short):
    task_dir = os.path.dirname(video_path)
    filename = os.path.basename(video_path)
    name = os.path.splitext(filename)[0]
    def progress_cb(p):
        pending_publish[task_id] = {"status": "processing", "progress": p}
    transcoder = Transcoder(progress_cb, is_short=is_short)
    duration, height = transcoder.get_video_info(video_path)
    pending_publish[task_id] = {"status": "transcoding", "progress": 0}
    hls_dir = transcoder.generate_hls(video_path, task_dir, duration, height)
    pending_publish[task_id] = {"status": "generating_covers", "progress": 100}
    covers_dir, best_cover = transcoder.generate_covers(video_path, task_dir, duration)
    preview_path = None
    if not is_short:
        preview_path = transcoder.generate_preview(video_path, task_dir, duration, name)
    covers = []
    for i in range(1, 11):
        cp = os.path.join(covers_dir, f"cover_{i}.webp")
        if os.path.exists(cp):
            covers.append({"index": i, "url": f"/api/preview/{task_id}/covers/cover_{i}.webp", "selected": i == best_cover})
    # Save metadata for recovery
    meta_path = os.path.join(task_dir, "task_meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({"is_short": is_short, "duration": duration, "filename": filename}, f)
    return {
        "status": "ready", "task_id": task_id, "filename": filename, "name": name,
        "duration": duration, "height": height, "is_short": is_short,
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
    data = request.json
    task_id = data.get('task_id')
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    task_data = pending_publish[task_id]
    if task_data.get("status") not in ("ready", "scheduled"):
        return jsonify({"error": "Video not ready"}), 400
    try:
        video_id = f"{'short_' if task_data['is_short'] else ''}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        hls_url = uploader.upload_hls(task_data['hls_dir'], video_id)
        uploader.upload_covers(task_data['covers_dir'], video_id)
        cover_url = f"/uploads/hls/{video_id}/covers/cover_{data.get('selected_cover', task_data['best_cover'])}.webp"
        preview_url = ""
        if task_data.get('preview_path'):
            preview_url = uploader.upload_preview(task_data['preview_path']) or ""
        import urllib.request
        video_data = {
            "title": data.get('title', task_data['name']),
            "hls_url": hls_url, "cover_url": cover_url, "preview_url": preview_url,
            "duration": task_data['duration'], "is_short": task_data['is_short'],
            "is_vip_only": data.get('is_vip_only', False),
            "coin_price": data.get('coin_price', 0),
            "free_preview_seconds": data.get('free_preview_seconds', 15),
            "status": "PUBLISHED",
        }
        if data.get('category_id'):
            video_data["category_id"] = data['category_id']
        if data.get('tag_ids'):
            video_data["tag_ids"] = data['tag_ids']
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/videos/direct-publish",
            data=json.dumps(video_data).encode('utf-8'),
            headers={"Content-Type": "application/json", "X-Transcode-Key": MAIN_SERVER['transcode_key']},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        queue.add_publish_history(0, task_data['filename'], data.get('title', task_data['name']),
                                  result.get("id"), task_data['is_short'], task_data['duration'], hls_url, cover_url)
        shutil.rmtree(os.path.join(DIRS["processing"], task_id), ignore_errors=True)
        del pending_publish[task_id]
        return jsonify({"success": True, "video_id": result.get("id")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reorder', methods=['POST'])
def reorder_tasks():
    queue.update_sort_order(request.json.get('task_ids', []))
    return jsonify({"success": True})


@app.route('/api/tasks')
def get_tasks():
    return jsonify({"tasks": queue.get_recent_tasks(50), "stats": queue.get_stats()})


@app.route('/api/queue')
def get_queue():
    # 从pending_publish获取正在转码的任务
    processing_tasks = []
    for tid, d in pending_publish.items():
        status = d.get("status", "")
        if status in ("processing", "transcoding", "generating_covers"):
            processing_tasks.append({
                "task_id": tid,
                "filename": d.get("filename", ""),
                "status": status,
                "progress": d.get("progress", 0),
            })
    return jsonify({"tasks": processing_tasks})


@app.route('/api/pending')
def get_pending():
    items = [{"task_id": tid, **{k: v for k, v in d.items() if k in ('filename', 'duration', 'is_short', 'covers', 'scheduled_at', 'status')}}
             for tid, d in pending_publish.items() if d.get("status") in ("ready", "scheduled")]
    return jsonify({"items": items})


@app.route('/api/set-type/<task_id>', methods=['POST'])
def set_video_type(task_id):
    """Set video type (short/long) for a pending task"""
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    data = request.json
    is_short = data.get('is_short', False)
    pending_publish[task_id]['is_short'] = is_short
    # Update metadata file
    task_dir = os.path.join(DIRS["processing"], task_id)
    meta_path = os.path.join(task_dir, "task_meta.json")
    try:
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        meta['is_short'] = is_short
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f)
    except:
        pass
    return jsonify({"success": True, "is_short": is_short})


@app.route('/api/history')
def get_history():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    return jsonify({"items": queue.get_publish_history(limit, (page-1)*limit), "stats": queue.get_history_stats()})


@app.route('/api/system')
def get_system_info():
    free_gb = get_free_disk_space()
    return jsonify({"disk_free_gb": round(free_gb, 2), "disk_warning": free_gb < 20, "disk_critical": free_gb < 10})


def run_web_ui(host='0.0.0.0', port=8080):
    ensure_dirs()
    recover_pending_tasks()
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_web_ui()
'''

# Write to file
path = 'transcode_service/web_ui.py'
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

if 'recover_pending_tasks' in c:
    print(f"OK: File created with recover_pending_tasks, size: {len(c)} bytes")
else:
    print("ERROR: recover_pending_tasks not found in file")

if __name__ == '__main__':
    pass
