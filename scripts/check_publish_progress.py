"""
检查发布进度
"""
import urllib.request
import json
import time

task_id = "20260122033237306288"

for i in range(60):  # 最多等待5分钟
    r = urllib.request.urlopen(f'http://198.176.60.121:8080/api/status/{task_id}', timeout=10)
    status = json.loads(r.read().decode())
    
    print(f"[{i*5}s] 状态: {status.get('status')}, 进度: {status.get('publish_progress', 'N/A')}")
    
    if status.get('status') not in ('publishing',):
        if status.get('status') == 'publish_failed':
            print(f"发布失败: {status.get('publish_error')}")
        break
    
    time.sleep(5)
else:
    print("超时")

# 最终检查
try:
    r = urllib.request.urlopen(f'http://198.176.60.121:8080/api/status/{task_id}', timeout=10)
    status = json.loads(r.read().decode())
    print(f"\n最终状态: {status}")
except:
    print("\n任务已完成（从pending中移除）")
