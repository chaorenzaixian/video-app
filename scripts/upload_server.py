# upload_server.py - 转码服务器上传接收服务
# 部署到转码服务器: D:\VideoTranscode\scripts\upload_server.py
# 运行: python upload_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有跨域

# 配置
UPLOAD_DIR = "D:\\VideoTranscode\\downloads"
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'avi', 'mov', 'mkv', 'flv'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # 10GB
API_KEY = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"  # 与转码密钥相同

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "service": "transcode-upload-server"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    """
    接收视频上传
    Headers: X-API-Key (必须)
    Form: file (视频文件), video_id (可选，用于回调)
    """
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    # 验证API密钥
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401
    
    # 检查文件
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"}), 400
    
    # 获取视频ID（用于命名和回调）
    video_id = request.form.get('video_id', '')
    
    # 生成文件名（使用video_id作为前缀，方便watcher识别）
    ext = os.path.splitext(file.filename)[1].lower()
    if video_id:
        filename = f"{video_id}{ext}"
    else:
        filename = f"{uuid.uuid4().hex}{ext}"
    
    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 保存文件
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        print(f"[Upload] 接收文件: {filename}, 大小: {file_size/1024/1024:.2f}MB")
        
        return jsonify({
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "size": file_size,
            "video_id": video_id,
            "message": "文件已接收，watcher将自动处理"
        })
        
    except Exception as e:
        print(f"[Error] 保存文件失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """获取转码服务器状态"""
    try:
        # 统计各目录文件数
        downloads = len([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]) if os.path.exists(UPLOAD_DIR) else 0
        processing_dir = "D:\\VideoTranscode\\processing"
        processing = len([f for f in os.listdir(processing_dir) if os.path.isfile(os.path.join(processing_dir, f))]) if os.path.exists(processing_dir) else 0
        
        return jsonify({
            "status": "running",
            "pending": downloads,
            "processing": processing,
            "upload_dir": UPLOAD_DIR
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("转码服务器上传接收服务")
    print("=" * 50)
    print(f"上传目录: {UPLOAD_DIR}")
    print(f"监听端口: 5000")
    print("=" * 50)
    
    # 确保目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 启动服务
    app.run(host='0.0.0.0', port=5000, threaded=True)
