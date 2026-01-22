"""
测试system API
"""
import urllib.request
import json

try:
    r = urllib.request.urlopen('http://198.176.60.121:8080/api/system', timeout=10)
    print(json.dumps(json.loads(r.read().decode()), indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP错误: {e.code}")
    print(f"错误内容: {e.read().decode()}")
except Exception as e:
    print(f"错误: {e}")
