"""
转码服务配置 - 优化版
"""
import os
import multiprocessing

# 基础目录
BASE_DIR = r"D:\VideoTranscode"

# 目录配置
DIRS = {
    "downloads_long": os.path.join(BASE_DIR, "downloads", "long"),
    "downloads_short": os.path.join(BASE_DIR, "downloads", "short"),
    "downloads_darkweb": os.path.join(BASE_DIR, "downloads", "darkweb"),
    "processing": os.path.join(BASE_DIR, "processing"),
    "completed_long": os.path.join(BASE_DIR, "completed", "long"),
    "completed_short": os.path.join(BASE_DIR, "completed", "short"),
    "completed_darkweb": os.path.join(BASE_DIR, "completed", "darkweb"),
    "logs": os.path.join(BASE_DIR, "logs"),
    "db": os.path.join(BASE_DIR, "data"),
    "uploads": os.path.join(BASE_DIR, "uploads"),  # 断点续传临时目录
}

# 数据库
DATABASE_PATH = os.path.join(DIRS["db"], "transcode.db")

# 主服务器配置
MAIN_SERVER = {
    "host": "38.47.218.137",
    "ssh_key": r"C:\server_key",
    "upload_base": "/www/wwwroot/video-app/backend/uploads",
    "api_base": "http://38.47.218.137/api/v1",  # 通过nginx 80端口访问
    "transcode_key": "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U",
}

# FFmpeg配置 - 优化版
FFMPEG = {
    "hls_time": 10,
    "crf": 23,
    "preset_long": "fast",        # 长视频用fast，速度快30%，质量几乎无差别
    "preset_short": "veryfast",   # 短视频用veryfast，速度更快
    "audio_bitrate": "128k",
    "cover_count": 10,
    "cover_quality": 85,
    "threads": 0,                 # 0=自动使用所有CPU核心
}

# 并行转码配置
PARALLEL = {
    "max_workers": min(3, max(1, multiprocessing.cpu_count() // 2)),  # 最多3个并行任务
    "enabled": True,
}

# 服务配置
SERVICE = {
    "name": "VideoTranscodeService",
    "display_name": "Video Transcode Service",
    "description": "自动视频转码服务 - 监控目录、转码、上传",
    "check_interval": 5,      # 缩短检查间隔
    "max_retries": 3,
    "web_port": 8080,
    "watchdog_interval": 60,  # 进程守护检查间隔
}

# 磁盘监控配置
DISK = {
    "min_free_gb": 10,        # 最小剩余空间(GB)
    "warning_free_gb": 20,    # 警告阈值(GB)
}

# 日志配置
LOGGING = {
    "max_size_mb": 10,        # 单个日志文件最大大小
    "backup_count": 5,        # 保留日志文件数量
    "cleanup_days": 30,       # 清理多少天前的日志
}

# 断点续传配置
UPLOAD = {
    "chunk_size": 5 * 1024 * 1024,  # 5MB分块
    "max_retries": 3,
}

# 确保目录存在
def ensure_dirs():
    for path in DIRS.values():
        os.makedirs(path, exist_ok=True)

# 获取磁盘剩余空间(GB)
def get_free_disk_space():
    import shutil
    total, used, free = shutil.disk_usage(BASE_DIR)
    return free / (1024 ** 3)

# 检查磁盘空间是否足够
def check_disk_space():
    free_gb = get_free_disk_space()
    if free_gb < DISK["min_free_gb"]:
        return False, f"磁盘空间不足: {free_gb:.1f}GB < {DISK['min_free_gb']}GB"
    if free_gb < DISK["warning_free_gb"]:
        return True, f"磁盘空间警告: {free_gb:.1f}GB"
    return True, None
