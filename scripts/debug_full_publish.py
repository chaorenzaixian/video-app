"""
调试完整发布流程
模拟转码服务的publish_video函数
"""
import urllib.request
import json
import sys

# 配置
TRANSCODE_SERVER = "http://198.176.60.121:8080"
MAIN_SERVER_API = "http://38.47.218.137/api/v1"
TRANSCODE_KEY = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"

def test_publish():
    # 1. 获取待发布列表
    print("=" * 50)
    print("1. 获取待发布列表")
    r = urllib.request.urlopen(f'{TRANSCODE_SERVER}/api/pending', timeout=10)
    pending = json.loads(r.read().decode())
    print(f"待发布数量: {len(pending)}")
    
    if not pending:
        print("没有待发布的视频")
        return
    
    task = pending[0]
    task_id = task['task_id']
    print(f"\n选择任务: {task_id} - {task.get('filename')}")
    print(f"  is_short: {task.get('is_short')}")
    print(f"  is_darkweb: {task.get('is_darkweb')}")
    print(f"  duration: {task.get('duration')}")
    
    # 2. 调用转码服务的发布API
    print("\n" + "=" * 50)
    print("2. 调用转码服务发布API")
    
    publish_data = {
        "task_id": task_id,
        "title": task.get('name', task.get('filename', 'test')),
        "description": "",
        "selected_cover": task.get('best_cover', 5),
        "is_vip_only": False,
        "is_featured": False,
        "coin_price": 0,
        "free_preview_seconds": 15,
    }
    
    print(f"发送数据: {json.dumps(publish_data, indent=2, ensure_ascii=False)}")
    
    req = urllib.request.Request(
        f'{TRANSCODE_SERVER}/api/publish',
        data=json.dumps(publish_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:  # 5分钟超时
            result = json.loads(resp.read().decode())
            print(f"\n发布成功: {result}")
    except urllib.error.HTTPError as e:
        print(f"\nHTTP错误: {e.code}")
        error_body = e.read().decode()
        print(f"错误内容: {error_body}")
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    test_publish()
