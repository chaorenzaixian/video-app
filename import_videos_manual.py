#!/usr/bin/env python3
"""
手动导入视频到数据库
在回调 API 部署之前使用
"""
import paramiko
import json

# 主服务器配置
MAIN_SERVER = "38.47.218.137"
SSH_KEY = "server_key"

def get_uploaded_videos():
    """获取已上传的视频列表"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(MAIN_SERVER, username='root', key_filename=SSH_KEY, timeout=30)
    
    videos = []
    
    # 获取短视频
    stdin, stdout, stderr = ssh.exec_command('ls /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null', timeout=30)
    shorts = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    for path in shorts:
        if path:
            name = path.split('/')[-1].replace('.mp4', '')
            videos.append({
                'filename': name,
                'is_short': True,
                'video_url': f'/uploads/shorts/{name}.mp4',
                'cover_url': f'/uploads/thumbnails/{name}.webp'
            })
    
    # 获取长视频 HLS
    stdin, stdout, stderr = ssh.exec_command('ls -d /www/wwwroot/video-app/backend/uploads/hls/*/ 2>/dev/null', timeout=30)
    hls_dirs = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    for path in hls_dirs:
        if path:
            name = path.rstrip('/').split('/')[-1]
            videos.append({
                'filename': name,
                'is_short': False,
                'hls_url': f'/uploads/hls/{name}/master.m3u8',
                'cover_url': f'/uploads/thumbnails/{name}.webp',
                'preview_url': f'/uploads/previews/{name}_preview.webm'
            })
    
    ssh.close()
    return videos

def main():
    print('📊 已上传的视频')
    print('=' * 60)
    
    videos = get_uploaded_videos()
    
    print(f'\n找到 {len(videos)} 个视频:\n')
    
    for i, v in enumerate(videos, 1):
        vtype = '短视频' if v['is_short'] else '长视频'
        print(f'{i}. [{vtype}] {v["filename"]}')
        if v['is_short']:
            print(f'   视频: {v["video_url"]}')
        else:
            print(f'   HLS: {v["hls_url"]}')
        print(f'   封面: {v["cover_url"]}')
        if v.get('preview_url'):
            print(f'   预览: {v["preview_url"]}')
        print()
    
    print('\n要导入这些视频到数据库，需要:')
    print('1. 在主服务器上重启后端服务以加载新的 API')
    print('2. 或者直接在数据库中插入记录')
    print('\nSQL 示例:')
    print('INSERT INTO videos (title, is_short, hls_url, cover_url, preview_url, status, uploader_id)')
    print('VALUES ("视频标题", 0, "/uploads/hls/xxx/master.m3u8", "/uploads/thumbnails/xxx.webp", "/uploads/previews/xxx_preview.webm", "REVIEWING", 1);')

if __name__ == '__main__':
    main()
