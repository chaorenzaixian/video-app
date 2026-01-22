"""
测试发布长视频
"""
import urllib.request
import json
import time

# 获取待发布的长视频
r = urllib.request.urlopen('http://198.176.60.121:8080/api/pending', timeout=10)
pending = json.loads(r.read().decode())

long_videos = [i for i in pending if not i.get('is_short')]
print(f"待发布长视频: {len(long_videos)}")

if not long_videos:
    print("没有待发布的长视频")
    exit()

# 选择第一个长视频
task = long_videos[0]
task_id = task['task_id']
print(f"\n选择: {task.get('filename')}")
print(f"时长: {task.get('duration', 0):.0f}秒")

# 发布
print("\n开始发布...")
data = {
    "task_id": task_id,
    "title": task.get('name', task.get('filename', 'test')),
    "selected_cover": task.get('best_cover', 5)
}

req = urllib.request.Request(
    'http://198.176.60.121:8080/api/publish',
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode())
    print(f"响应: {result}")

# 监控进度
print("\n监控发布进度...")
for i in range(120):  # 最多10分钟
    time.sleep(5)
    try:
        r = urllib.request.urlopen(f'http://198.176.60.121:8080/api/status/{task_id}', timeout=10)
        status = json.loads(r.read().decode())
        progress = status.get('publish_progress', status.get('progress', 'N/A'))
        print(f"[{(i+1)*5}s] 状态: {status.get('status')} | 进度: {progress}")
        
        if status.get('status') == 'publish_failed':
            print(f"发布失败: {status.get('publish_error')}")
            break
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[{(i+1)*5}s] 发布完成！（任务已移除）")
            break
        raise
