"""测试队列显示"""
import requests
import time
import threading

def check_queue():
    """持续检查队列"""
    for i in range(30):
        try:
            queue = requests.get("http://198.176.60.121:8080/api/queue", timeout=5).json()
            pending = requests.get("http://198.176.60.121:8080/api/pending", timeout=5).json()
            
            # 统计pending中的状态
            statuses = {}
            for item in pending:
                status = item.get('status', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"[{i+1}] Queue: {len(queue)}, Pending: {len(pending)}, Statuses: {statuses}")
            
            if queue:
                for item in queue:
                    print(f"    Queue item: {item.get('filename')}: {item.get('status')} ({item.get('progress', 0):.1f}%)")
        except Exception as e:
            print(f"[{i+1}] Error: {e}")
        
        time.sleep(1)

# 启动检查线程
checker = threading.Thread(target=check_queue)
checker.start()

# 等待1秒后添加视频
time.sleep(1)
print("\n=== 添加视频 ===")
video_path = r"D:\视频\萝莉\唐伯虎 爆操极品美女小姐姐，白丝袜包裹着白虎穴，肌肤嫩滑如玉，全身散发着青春气息.mp4"
response = requests.post(
    "http://198.176.60.121:8080/api/add-local",
    json={"path": video_path, "video_type": "long"},
    timeout=30
)
result = response.json()
print(f"添加结果: task_id={result.get('tasks', [{}])[0].get('task_id')}")

# 等待检查线程完成
checker.join()
