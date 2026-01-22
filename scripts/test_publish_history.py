"""测试发布历史API"""
import urllib.request
import json

TRANSCODE_URL = "http://198.176.60.121:8080"

def test_history():
    """测试发布历史API"""
    print("=" * 50)
    print("测试发布历史API")
    print("=" * 50)
    
    try:
        # 获取发布历史
        req = urllib.request.Request(f"{TRANSCODE_URL}/api/history")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        print(f"\n响应数据类型: {type(data)}")
        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
        
        if isinstance(data, dict):
            items = data.get('items', [])
            stats = data.get('stats', {})
            print(f"\n统计信息:")
            print(f"  - 今日: {stats.get('today', 0)}")
            print(f"  - 本周: {stats.get('this_week', 0)}")
            print(f"  - 总计: {stats.get('total', 0)}")
            print(f"\n历史记录数量: {len(items)}")
            
            if items:
                print("\n最近5条记录:")
                for i, item in enumerate(items[:5]):
                    print(f"  {i+1}. {item.get('title', item.get('filename', 'N/A'))} - {item.get('published_at', 'N/A')}")
        else:
            print(f"意外的响应格式: {type(data)}")
            
    except Exception as e:
        print(f"错误: {e}")

def test_pending():
    """测试待发布API"""
    print("\n" + "=" * 50)
    print("测试待发布API")
    print("=" * 50)
    
    try:
        req = urllib.request.Request(f"{TRANSCODE_URL}/api/pending")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        print(f"\n待发布数量: {len(data) if isinstance(data, list) else 'N/A'}")
        
        if isinstance(data, list) and data:
            print("\n待发布任务:")
            for i, item in enumerate(data[:5]):
                print(f"  {i+1}. {item.get('filename', 'N/A')} - 状态: {item.get('status', 'N/A')}")
                
    except Exception as e:
        print(f"错误: {e}")

def test_system():
    """测试系统信息API"""
    print("\n" + "=" * 50)
    print("测试系统信息API")
    print("=" * 50)
    
    try:
        req = urllib.request.Request(f"{TRANSCODE_URL}/api/system")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        print(f"\n系统信息:")
        print(f"  - 磁盘可用: {data.get('disk_free_gb', 0)} GB")
        print(f"  - 待发布数量: {data.get('pending_count', 0)}")
        print(f"  - 队列数量: {data.get('queue_count', 0)}")
        print(f"  - 服务版本: {data.get('service_version', 'N/A')}")
                
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_system()
    test_pending()
    test_history()
