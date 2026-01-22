"""
调试发布422错误
"""
import urllib.request
import json

# 1. 获取待发布列表
print("=" * 50)
print("1. 获取待发布列表")
r = urllib.request.urlopen('http://198.176.60.121:8080/api/pending', timeout=10)
pending = json.loads(r.read().decode())
print(f"待发布数量: {len(pending)}")

if not pending:
    print("没有待发布的视频")
    exit()

task = pending[0]
print(f"\n任务详情:")
for k, v in task.items():
    print(f"  {k}: {v}")

# 2. 模拟发布流程，检查每一步
print("\n" + "=" * 50)
print("2. 测试直接调用主服务器API")

# 构造测试数据
video_data = {
    "title": task.get('name', 'test'),
    "description": "",
    "hls_url": f"/uploads/hls/test_{task['task_id']}/master.m3u8",
    "cover_url": f"/uploads/hls/test_{task['task_id']}/covers/cover_5.webp",
    "preview_url": "",
    "duration": task.get('duration', 0),
    "is_short": task.get('is_short', False),
    "is_vip_only": False,
    "is_featured": False,
    "coin_price": 0,
    "free_preview_seconds": 15,
    "status": "PUBLISHED",
}

print(f"\n发送数据:")
print(json.dumps(video_data, indent=2, ensure_ascii=False))

# 调用主服务器API
MAIN_SERVER_API = "http://38.47.218.137/api/v1"  # 通过nginx 80端口
TRANSCODE_KEY = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"

req = urllib.request.Request(
    f"{MAIN_SERVER_API}/admin/videos/direct-publish",
    data=json.dumps(video_data).encode('utf-8'),
    headers={
        "Content-Type": "application/json",
        "X-Transcode-Key": TRANSCODE_KEY
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        print(f"\n发布成功: {result}")
except urllib.error.HTTPError as e:
    print(f"\nHTTP错误: {e.code}")
    error_body = e.read().decode()
    print(f"错误内容: {error_body}")
    
    # 尝试解析JSON错误
    try:
        error_json = json.loads(error_body)
        print(f"\n解析后的错误:")
        print(json.dumps(error_json, indent=2, ensure_ascii=False))
    except:
        pass
except Exception as e:
    print(f"\n错误: {e}")
