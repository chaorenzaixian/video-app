"""
修复转码服务器的uploader
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 上传密钥文件
    print('上传密钥文件...')
    with open('server_key_new', 'r') as f:
        key_content = f.read()
    
    with sftp.file('D:/VideoTranscode/server_key', 'w') as f:
        f.write(key_content)
    print('密钥已上传到 D:/VideoTranscode/server_key')
    
    # 更新config.py - 修改密钥路径
    print('更新config.py...')
    config_content = '''"""
转码服务配置 - 优化版
"""
import os
import multiprocessing

# 基础目录
BASE_DIR = r"D:\\VideoTranscode"

# 目录配置
DIRS = {
    "downloads_long": os.path.join(BASE_DIR, "downloads", "long"),
    "downloads_short": os.path.join(BASE_DIR, "downloads", "short"),
    "processing": os.path.join(BASE_DIR, "processing"),
    "completed_long": os.path.join(BASE_DIR, "completed", "long"),
    "completed_short": os.path.join(BASE_DIR, "completed", "short"),
    "logs": os.path.join(BASE_DIR, "logs"),
    "db": os.path.join(BASE_DIR, "data"),
    "uploads": os.path.join(BASE_DIR, "uploads"),
}

# 数据库
DATABASE_PATH = os.path.join(DIRS["db"], "transcode.db")

# 主服务器配置
MAIN_SERVER = {
    "host": "38.47.218.137",
    "ssh_key": r"D:\\VideoTranscode\\server_key",
    "upload_base": "/www/wwwroot/video-app/backend/uploads",
    "api_base": "http://38.47.218.137:8000/api/v1",
    "transcode_key": "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U",
}

# FFmpeg配置
FFMPEG = {
    "hls_time": 10,
    "crf": 23,
    "preset_long": "medium",
    "preset_short": "veryfast",
    "audio_bitrate": "128k",
    "cover_count": 10,
    "cover_quality": 85,
}

# 并行转码配置
PARALLEL = {
    "max_workers": min(3, max(1, multiprocessing.cpu_count() // 2)),
    "enabled": True,
}

# 服务配置
SERVICE = {
    "name": "VideoTranscodeService",
    "display_name": "Video Transcode Service",
    "description": "自动视频转码服务",
    "check_interval": 5,
    "max_retries": 3,
    "web_port": 8080,
    "watchdog_interval": 60,
}

# 磁盘监控配置
DISK = {
    "min_free_gb": 10,
    "warning_free_gb": 20,
}

# 日志配置
LOGGING = {
    "max_size_mb": 10,
    "backup_count": 5,
    "cleanup_days": 30,
}

# 断点续传配置
UPLOAD = {
    "chunk_size": 5 * 1024 * 1024,
    "max_retries": 3,
}

def ensure_dirs():
    for path in DIRS.values():
        os.makedirs(path, exist_ok=True)

def get_free_disk_space():
    import shutil
    total, used, free = shutil.disk_usage(BASE_DIR)
    return free / (1024 ** 3)

def check_disk_space():
    free_gb = get_free_disk_space()
    if free_gb < DISK["min_free_gb"]:
        return False, f"磁盘空间不足: {free_gb:.1f}GB"
    if free_gb < DISK["warning_free_gb"]:
        return True, f"磁盘空间警告: {free_gb:.1f}GB"
    return True, None
'''
    
    with sftp.file('D:/VideoTranscode/service/config.py', 'w') as f:
        f.write(config_content)
    print('config.py已更新')
    
    # 上传新的uploader.py
    print('上传uploader.py...')
    with open('transcode_service/uploader.py', 'r', encoding='utf-8') as f:
        uploader_content = f.read()
    
    with sftp.file('D:/VideoTranscode/service/uploader.py', 'w') as f:
        f.write(uploader_content)
    print('uploader.py已上传')
    
    sftp.close()
    
    # 重启服务
    print('重启服务...')
    stdin, stdout, stderr = client.exec_command('taskkill /f /im python.exe 2>nul')
    import time
    time.sleep(2)
    
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode && start /b pythonw service\\web_ui.py')
    time.sleep(3)
    
    # 检查
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080 | findstr LISTENING')
    result = stdout.read().decode('gbk', errors='ignore')
    print('服务状态:', '运行中' if 'LISTENING' in result else '启动失败')
    
    client.close()
    print('完成!')

if __name__ == '__main__':
    main()
