"""
查看发布状态
"""
import urllib.request
import json

# 获取转码队列（包含正在发布的）
r = urllib.request.urlopen('http://198.176.60.121:8080/api/queue', timeout=10)
queue = json.loads(r.read().decode())

print('=== 转码队列 ===')
for item in queue:
    status = item.get('status', '')
    is_short = item.get('is_short', False)
    video_type = '短视频' if is_short else '长视频'
    progress = item.get('publish_progress', item.get('progress', ''))
    error = item.get('publish_error', '')
    filename = item.get('filename', '')[:30]
    print(f'{video_type} | {filename} | 状态: {status} | 进度: {progress}')
    if error:
        print(f'  错误: {error}')

# 统计
long_publishing = [i for i in queue if not i.get('is_short') and i.get('status') == 'publishing']
short_publishing = [i for i in queue if i.get('is_short') and i.get('status') == 'publishing']
print(f'\n正在发布的长视频: {len(long_publishing)}')
print(f'正在发布的短视频: {len(short_publishing)}')

# 获取待发布
r2 = urllib.request.urlopen('http://198.176.60.121:8080/api/pending', timeout=10)
pending = json.loads(r2.read().decode())
long_pending = [i for i in pending if not i.get('is_short')]
short_pending = [i for i in pending if i.get('is_short')]
print(f'\n待发布长视频: {len(long_pending)}')
print(f'待发布短视频: {len(short_pending)}')
