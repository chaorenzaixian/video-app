"""测试暗网视频发布"""
import urllib.request
import json

# 测试发布暗网视频
task_id = "20260120210025604120"
publish_data = {
    "task_id": task_id,
    "title": "测试暗网视频发布",
    "description": "测试描述",
    "category_id": None,
    "tag_ids": None,
    "selected_cover": 5,
    "is_featured": False
}

url = "http://198.176.60.121:8080/api/publish-darkweb"
print(f"POST {url}")
print(f"Data: {json.dumps(publish_data, ensure_ascii=False)}")

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(publish_data).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = resp.read().decode('utf-8')
        print(f"Result: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
