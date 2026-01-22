"""测试任务状态"""
import requests
import time

# 添加视频
print("添加视频...")
video_path = r"D:\视频\萝莉\尾随白丝洛丽塔少萝宝宝回家，最后把她按在落地窗前爆操，连连求饶.mp4"
response = requests.post(
    "http://198.176.60.121:8080/api/add-local",
    json={"path": video_path, "video_type": "long"},
    timeout=30
)
result = response.json()
task_id = result.get('tasks', [{}])[0].get('task_id')
print(f"Task ID: {task_id}")

# 持续检查任务状态
print("\n持续检查任务状态:")
for i in range(60):
    try:
        # 检查任务状态
        status_resp = requests.get(f"http://198.176.60.121:8080/api/status/{task_id}", timeout=5)
        status = status_resp.json()
        
        # 检查队列
        queue = requests.get("http://198.176.60.121:8080/api/queue", timeout=5).json()
        
        # 检查pending
        pending = requests.get("http://198.176.60.121:8080/api/pending", timeout=5).json()
        
        # 检查这个任务是否在pending中
        in_pending = any(p.get('task_id') == task_id for p in pending)
        in_queue = any(q.get('task_id') == task_id for q in queue)
        
        print(f"[{i+1:2d}] Status: {status.get('status'):20s} Progress: {status.get('progress', 0):6.2f}% | Queue: {len(queue)} | Pending: {len(pending)} | In Queue: {in_queue} | In Pending: {in_pending}")
        
        if status.get('status') == 'ready':
            print("\n转码完成!")
            break
    except Exception as e:
        print(f"[{i+1:2d}] Error: {e}")
    
    time.sleep(1)
