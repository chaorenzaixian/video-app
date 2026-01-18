#!/usr/bin/env python3
"""最终转码监控系统测试"""
import requests
import json

print("=" * 60)
print("转码监控系统最终测试")
print("=" * 60)

# 1. 测试转码服务器状态API
print("\n1. 测试转码服务器状态API (直接访问)")
TRANSCODE_API = 'http://198.176.60.121:5001'
SECRET_KEY = 'vYTWoms4FKOqySca1jCLtNHRVz3BAI6U'
headers = {'X-Transcode-Key': SECRET_KEY}

try:
    r = requests.get(f'{TRANSCODE_API}/health', timeout=10)
    print(f"   健康检查: {r.json()}")
    
    r = requests.get(f'{TRANSCODE_API}/status', headers=headers, timeout=10)
    data = r.json()
    print(f"   服务状态: {data.get('service', {}).get('status', 'unknown')}")
    print(f"   待处理队列: 短视频={data.get('queue', {}).get('short_pending_count', 0)}, 长视频={data.get('queue', {}).get('long_pending_count', 0)}")
    print(f"   正在处理: {data.get('queue', {}).get('processing_count', 0)}")
    print(f"   已完成: 短视频={data.get('completed', {}).get('short_count', 0)}, 长视频={data.get('completed', {}).get('long_count', 0)}")
    print(f"   磁盘空间: {data.get('disk', [])}")
    print("   ✓ 转码服务器状态API正常")
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 2. 测试日志API
print("\n2. 测试转码服务器日志API")
try:
    r = requests.get(f'{TRANSCODE_API}/logs', headers=headers, params={'lines': 5}, timeout=10)
    data = r.json()
    print(f"   日志条数: {data.get('total', 0)}")
    for log in data.get('logs', [])[:3]:
        msg = log.get('message', '')[:40]
        print(f"   [{log.get('level')}] {log.get('timestamp')} - {msg}...")
    print("   ✓ 日志API正常")
except Exception as e:
    print(f"   ✗ 错误: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
print("\n后续步骤:")
print("1. 访问管理后台: http://38.47.218.137/admin")
print("2. 登录后进入: 数据中心 -> 转码监控")
print("3. 查看实时转码状态、队列、日志等信息")
