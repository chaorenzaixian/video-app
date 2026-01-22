"""
添加暗网视频支持到web_ui.py
"""
import re

# 读取原文件
with open('transcode_service/web_ui.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 修改recover_pending_tasks - 添加is_darkweb
content = content.replace(
    'is_short = False',
    'is_short = False\n            is_darkweb = False'
)
content = content.replace(
    "is_short = meta.get('is_short', False)",
    "is_short = meta.get('is_short', False)\n                        is_darkweb = meta.get('is_darkweb', False)"
)
content = content.replace(
    '"duration": duration, "height": 0, "is_short": is_short,',
    '"duration": duration, "height": 0, "is_short": is_short, "is_darkweb": is_darkweb,'
)
content = content.replace(
    'print(f"Recovered: {task_dir} - {filename} (short={is_short})")',
    'print(f"Recovered: {task_dir} - {filename} (short={is_short}, darkweb={is_darkweb})")'
)

# 2. 修改upload_video - 支持video_type
content = content.replace(
    "is_short = request.form.get('is_short', 'false') == 'true'",
    '''video_type = request.form.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb\''''
)

# 3. 修改add_local_file - 支持video_type
content = content.replace(
    "is_short = data.get('is_short', False)",
    '''video_type = data.get('video_type', 'long')
    is_short = video_type == 'short'
    is_darkweb = video_type == 'darkweb\''''
)

# 4. 修改transcode调用 - 传递is_darkweb
content = content.replace(
    'threading.Thread(target=transcode, args=(task_id, video_path, is_short)).start()',
    'threading.Thread(target=transcode, args=(task_id, video_path, is_short, is_darkweb)).start()'
)

# 5. 修改process_video函数签名和内容
content = content.replace(
    'def process_video(task_id, video_path, is_short):',
    'def process_video(task_id, video_path, is_short, is_darkweb=False):'
)
content = content.replace(
    'json.dump({"is_short": is_short, "duration": duration, "filename": filename}, f)',
    'json.dump({"is_short": is_short, "is_darkweb": is_darkweb, "duration": duration, "filename": filename}, f)'
)
content = content.replace(
    '"duration": duration, "height": height, "is_short": is_short,',
    '"duration": duration, "height": height, "is_short": is_short, "is_darkweb": is_darkweb,'
)

# 6. 修改get_pending - 添加is_darkweb到返回字段
content = content.replace(
    "if k in ('filename', 'duration', 'is_short', 'covers', 'scheduled_at', 'status')",
    "if k in ('filename', 'duration', 'is_short', 'is_darkweb', 'covers', 'scheduled_at', 'status')"
)

# 7. 修改get_categories - 添加暗网分类
old_categories = '''@app.route('/api/categories')
def get_categories():
    import urllib.request'''

new_categories = '''@app.route('/api/categories')
def get_categories():
    import urllib.request
    darkweb_categories = []
    try:
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/darkweb/categories",
            headers={"X-Transcode-Key": MAIN_SERVER['transcode_key']}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            darkweb_categories = json.loads(resp.read().decode())
    except:
        pass'''

content = content.replace(old_categories, new_categories)

# 8. 修改categories返回值
content = content.replace(
    'return jsonify({"video_categories": [], "short_categories": []})',
    'return jsonify({"video_categories": [], "short_categories": [], "darkweb_categories": darkweb_categories})'
)

# 找到video_categories和short_categories的返回并添加darkweb
# 这个比较复杂，需要找到正确的位置
old_return = 'return jsonify({"video_categories": video_categories, "short_categories": short_categories})'
new_return = 'return jsonify({"video_categories": video_categories, "short_categories": short_categories, "darkweb_categories": darkweb_categories})'
content = content.replace(old_return, new_return)

# 9. 修改get_tags - 添加暗网标签
old_tags = '''@app.route('/api/tags')
def get_tags():
    import urllib.request'''

new_tags = '''@app.route('/api/tags')
def get_tags():
    import urllib.request
    darkweb_tags = []
    try:
        req = urllib.request.Request(
            f"{MAIN_SERVER['api_base']}/admin/darkweb/tags",
            headers={"X-Transcode-Key": MAIN_SERVER['transcode_key']}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            darkweb_tags = data.get('items', []) if isinstance(data, dict) else data
    except:
        pass'''

content = content.replace(old_tags, new_tags)

# 修改tags返回值
content = content.replace(
    'return jsonify({"tags": []})',
    'return jsonify({"tags": [], "darkweb_tags": darkweb_tags})'
)
content = content.replace(
    'return jsonify({"tags": tags})',
    'return jsonify({"tags": tags, "darkweb_tags": darkweb_tags})'
)

# 10. 添加暗网视频发布API - 在publish_video之后添加
publish_darkweb_api = '''

@app.route('/api/publish-darkweb', methods=['POST'])
def publish_darkweb_video():
    """发布暗网视频到主服务器"""
    data = request.json
    task_id = data.get('task_id')
    if task_id not in pending_publish:
        return jsonify({"error": "Task not found"}), 404
    task_data = pending_publish[task_id]
    if task_data.get("status") not in ("ready", "scheduled"):
        return jsonify({"error": "Video not ready"}), 400
    try:
        video_id = f"darkweb_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        # 上传到暗网目录
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
            "hls_url": hls_url, 
            "cover_url": cover_url, 
            "preview_url": preview_url,
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

'''

# 在 @app.route('/api/reorder' 之前插入
insert_marker = "@app.route('/api/reorder'"
insert_pos = content.find(insert_marker)
if insert_pos != -1:
    content = content[:insert_pos] + publish_darkweb_api + content[insert_pos:]

# 写回文件
with open('transcode_service/web_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Added darkweb video support to web_ui.py")
