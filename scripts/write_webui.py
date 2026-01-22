#!/usr/bin/env python3
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
            print(f"Recovered: {task_dir} - {filename}")


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
    local_path = data.get('path', '').strip()
    video_type = data.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb'
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
    pending_publish[task_id] = {"status": "uploading", "progress": 0, "filename": filename}
    def transcode(tid, vpath, short, darkweb):
        try:
            result = process_video(tid, vpath, short, darkweb)
            pending_publish[tid] = result
        except Exception as e:
            pending_publish[tid] = {"error": str(e), "status": "failed"}
    threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()
    return jsonify({"success": True, "task_id": task_id, "filename": filename})


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
            "description": data.get('description', ''),
            "hls_url": hls_url, "cover_url": cover_url, "preview_url": preview_url,
            "duration": task_data['duration'], "is_short": task_data['is_short'],
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
            f"{MAIN_SERVER['api_base']}/admin/darkweb/videos",
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


@app.route('/api/pending')
def get_pending():
    items = [{"task_id": tid, **{k: v for k, v in d.items() if k in ('filename', 'duration', 'is_short', 'is_darkweb', 'covers', 'scheduled_at', 'status')}}
             for tid, d in pending_publish.items() if d.get("status") in ("ready", "scheduled")]
    return jsonify({"items": items})


@app.route('/api/queue')
def get_queue():
    processing_tasks = []
    for tid, d in pending_publish.items():
        status = d.get("status", "")
        if status in ("uploading", "processing", "transcoding", "generating_covers"):
            processing_tasks.append({"task_id": tid, "filename": d.get("filename", ""), "status": status, "progress": d.get("progress", 0)})
    return jsonify({"tasks": processing_tasks})


@app.route('/api/delete/<task_id>', methods=['DELETE'])
def delete_pending(task_id):
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    try:
        task_dir = os.path.join(DIRS["processing"], task_id)
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir, ignore_errors=True)
        del pending_publish[task_id]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/system')
def get_system_info():
    free_gb = get_free_disk_space()
    return jsonify({"disk_free_gb": round(free_gb, 2), "disk_warning": free_gb < 20, "disk_critical": free_gb < 10})


@app.route('/api/history')
def get_history():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    return jsonify({"items": queue.get_publish_history(limit, (page-1)*limit), "stats": queue.get_history_stats()})


def run_web_ui(host='0.0.0.0', port=8080):
    ensure_dirs()
    recover_pending_tasks()
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    run_web_ui()
'''

with open('transcode_service/web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written {len(content)} bytes')
