"""测试添加视频到转码队列"""
import requests
import json
import time

# 添加一个大视频文件 (1.2GB)
video_path = r"D:\视频\萝莉\Zoey 推特福利姬，户外露出，地下室停车场被金主调教.mp4"

print(f"添加视频: {video_path}")
response = requests.post(
    "http://198.176.60.121:8080/api/add-local",
    json={"path": video_path, "video_type": "long"},
    timeout=30
)
result = response.json()
print(f"响应: {result}")
task_id = result.get('tasks', [{}])[0].get('task_id')

# 立即检查队列
print("\n立即检查转码队列:")
queue_response = requests.get("http://198.176.60.121:8080/api/queue", timeout=10)
queue = queue_response.json()
print(f"队列数量: {len(queue)}")
for item in queue:
    print(f"  - {item.get('filename')}: {item.get('status')} ({item.get('progress', 0)}%)")

# 持续检查状态
if task_id:
    for i in range(10):
        time.sleep(3)
        status_response = requests.get(f"http://198.176.60.121:8080/api/status/{task_id}", timeout=10)
        status = status_response.json()
        print(f"\n[{i+1}] 任务状态: {status.get('status')} - 进度: {status.get('progress', 0)}%")
        
        queue_response = requests.get("http://198.176.60.121:8080/api/queue", timeout=10)
        queue = queue_response.json()
        print(f"    队列数量: {len(queue)}")
        
        if status.get('status') == 'ready':
            print("转码完成!")
            break
