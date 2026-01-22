import urllib.request
import json

# 获取待发布列表
r = urllib.request.urlopen('http://198.176.60.121:8080/api/pending', timeout=10)
pending = json.loads(r.read().decode())
print(f"待发布数量: {len(pending)}")

if pending:
    task = pending[0]
    print(f"测试任务: {task.get('task_id')} - {task.get('filename')}")
    
    # 尝试发布
    data = {
        "task_id": task['task_id'],
        "title": task.get('name', task.get('filename', 'test')),
        "selected_cover": task.get('best_cover', 5)
    }
    
    req = urllib.request.Request(
        'http://198.176.60.121:8080/api/publish',
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            print(f"发布成功: {result}")
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code}")
        print(f"错误内容: {e.read().decode()}")
    except Exception as e:
        print(f"错误: {e}")
