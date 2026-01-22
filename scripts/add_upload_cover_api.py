"""
添加封面上传API到web_ui.py
"""
import os

# 读取原文件
with open('transcode_service/web_ui.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 要插入的新API代码
new_api = '''
@app.route('/api/upload-cover', methods=['POST'])
def upload_cover():
    """Upload custom cover image for a task"""
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
    
    # 保存到任务的covers目录
    task_dir = os.path.join(DIRS["processing"], task_id)
    covers_dir = os.path.join(task_dir, "covers")
    
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir)
    
    # 转换为webp格式保存
    import subprocess
    from werkzeug.utils import secure_filename
    
    # 先保存原始文件
    temp_path = os.path.join(covers_dir, "temp_upload" + os.path.splitext(cover_file.filename)[1])
    cover_file.save(temp_path)
    
    # 转换为webp
    output_path = os.path.join(covers_dir, "custom_cover.webp")
    try:
        # 使用ffmpeg转换
        cmd = [
            "ffmpeg", "-y", "-i", temp_path,
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-q:v", "85",
            output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        
        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if os.path.exists(output_path):
            return jsonify({
                "success": True,
                "url": f"/api/preview/{task_id}/covers/custom_cover.webp"
            })
        else:
            return jsonify({"error": "Failed to convert image"}), 500
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500

'''

# 找到插入位置 - 在 @app.route('/api/schedule' 之前
insert_marker = "@app.route('/api/schedule'"
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("ERROR: Could not find insert position")
    exit(1)

# 插入新代码
new_content = content[:insert_pos] + new_api + content[insert_pos:]

# 写回文件
with open('transcode_service/web_ui.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: Added /api/upload-cover API")
print(f"Inserted at position {insert_pos}")
