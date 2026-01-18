#!/usr/bin/env python3
"""
转码服务器状态API
部署在转码服务器上，提供状态查询接口
"""
from flask import Flask, jsonify, request
import os
import subprocess
import glob

app = Flask(__name__)

BASE_DIR = r"D:\VideoTranscode"
SECRET_KEY = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"


def verify_key():
    """验证API密钥"""
    key = request.headers.get('X-Transcode-Key')
    return key == SECRET_KEY


@app.route('/status', methods=['GET'])
def get_status():
    """获取转码系统状态"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 检查watcher服务状态
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'VideoWatcherService', '/fo', 'list'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        task_running = '正在运行' in result.stdout
    except:
        task_running = False
    
    # 检查PowerShell进程
    try:
        result = subprocess.run(
            ['tasklist', '/fi', 'imagename eq powershell.exe', '/fo', 'csv'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        ps_count = result.stdout.count('powershell.exe')
    except:
        ps_count = 0
    
    # 获取队列文件
    def get_files(path, pattern='*.mp4'):
        try:
            files = glob.glob(os.path.join(path, pattern))
            return [os.path.basename(f) for f in files]
        except:
            return []
    
    def count_dirs(path):
        try:
            return len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
        except:
            return 0
    
    # 获取磁盘空间
    disk_info = []
    for drive in ['C:', 'D:']:
        try:
            import shutil
            total, used, free = shutil.disk_usage(drive)
            disk_info.append({
                'drive': drive,
                'free_gb': round(free / (1024**3), 1),
                'total_gb': round(total / (1024**3), 1),
                'used_percent': round(used / total * 100, 1)
            })
        except:
            pass
    
    return jsonify({
        'service': {
            'watcher_running': task_running,
            'powershell_processes': ps_count,
            'status': 'running' if task_running and ps_count > 0 else 'stopped'
        },
        'queue': {
            'short_pending': get_files(os.path.join(BASE_DIR, 'downloads', 'short')),
            'long_pending': get_files(os.path.join(BASE_DIR, 'downloads', 'long')),
            'processing': get_files(os.path.join(BASE_DIR, 'processing')),
            'short_pending_count': len(get_files(os.path.join(BASE_DIR, 'downloads', 'short'))),
            'long_pending_count': len(get_files(os.path.join(BASE_DIR, 'downloads', 'long'))),
            'processing_count': len(get_files(os.path.join(BASE_DIR, 'processing')))
        },
        'completed': {
            'short_count': count_dirs(os.path.join(BASE_DIR, 'completed', 'short')),
            'long_count': count_dirs(os.path.join(BASE_DIR, 'completed', 'long'))
        },
        'disk': disk_info
    })


@app.route('/logs', methods=['GET'])
def get_logs():
    """获取转码日志"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    lines = request.args.get('lines', 50, type=int)
    log_file = os.path.join(BASE_DIR, 'logs', 'watcher.log')
    
    log_entries = []
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    timestamp = parts[0].strip()
                    message = parts[1].strip()
                    
                    level = 'info'
                    if 'Error' in message or 'Failed' in message:
                        level = 'error'
                    elif 'OK' in message or 'Done' in message:
                        level = 'success'
                    
                    log_entries.append({
                        'timestamp': timestamp,
                        'message': message,
                        'level': level
                    })
                else:
                    log_entries.append({
                        'timestamp': '',
                        'message': line,
                        'level': 'info'
                    })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'logs': log_entries,
        'total': len(log_entries)
    })


@app.route('/service/restart', methods=['POST'])
def restart_service():
    """重启Watcher服务"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # 停止现有进程
        subprocess.run(['taskkill', '/f', '/im', 'powershell.exe'], 
                      capture_output=True, errors='ignore')
        
        import time
        time.sleep(2)
        
        # 重新启动
        subprocess.run(['schtasks', '/run', '/tn', 'VideoWatcherService'],
                      capture_output=True, errors='ignore')
        
        time.sleep(3)
        
        # 检查状态
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'VideoWatcherService', '/fo', 'list'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        running = '正在运行' in result.stdout
        
        return jsonify({
            'success': True,
            'running': running,
            'message': '服务已重启' if running else '服务重启中...'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
