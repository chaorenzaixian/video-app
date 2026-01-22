"""分步测试上传"""
import paramiko
import json
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
import time
sys.path.insert(0, r'D:\\VideoTranscode\\service')

from config import DIRS, MAIN_SERVER
from uploader import Uploader
import os
import json
import urllib.request

print("=== 分步测试发布流程 ===")

# 获取任务信息
processing_dir = DIRS["processing"]
task_id = "20260120143014814762"  # 使用已知有封面的任务
task_path = os.path.join(processing_dir, task_id)

print(f"任务: {task_id}")

hls_dir = os.path.join(task_path, "hls")
covers_dir = os.path.join(task_path, "covers")

print(f"HLS目录: {hls_dir}")
print(f"  存在: {os.path.exists(hls_dir)}")
print(f"封面目录: {covers_dir}")
print(f"  存在: {os.path.exists(covers_dir)}")

# 统计文件
if os.path.exists(hls_dir):
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(hls_dir):
        for f in files:
            file_count += 1
            total_size += os.path.getsize(os.path.join(root, f))
    print(f"HLS文件数: {file_count}, 总大小: {total_size / 1024 / 1024:.1f} MB")

# 测试上传
uploader = Uploader()
video_id = f"test_{int(time.time())}"

print(f"\\n=== 步骤1: 上传HLS ===")
start = time.time()
try:
    hls_url = uploader.upload_hls(hls_dir, video_id)
    print(f"HLS上传完成: {hls_url}")
    print(f"耗时: {time.time() - start:.1f}秒")
except Exception as e:
    print(f"HLS上传失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\\n=== 步骤2: 上传封面 ===")
start = time.time()
try:
    covers_url = uploader.upload_covers(covers_dir, video_id)
    print(f"封面上传完成: {covers_url}")
    print(f"耗时: {time.time() - start:.1f}秒")
except Exception as e:
    print(f"封面上传失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\\n=== 步骤3: 调用主服务器API ===")
video_data = {
    "title": "测试视频",
    "description": "",
    "hls_url": f"/uploads/hls/{video_id}/master.m3u8",
    "cover_url": f"/uploads/hls/{video_id}/covers/cover_5.webp",
    "preview_url": "",
    "duration": 90,
    "is_short": False,
    "is_vip_only": False,
    "is_featured": False,
    "coin_price": 0,
    "free_preview_seconds": 15,
    "status": "PUBLISHED",
}

print(f"API: {MAIN_SERVER['api_base']}/admin/videos/direct-publish")
print(f"数据: {json.dumps(video_data, ensure_ascii=False)[:200]}...")

start = time.time()
try:
    req = urllib.request.Request(
        f"{MAIN_SERVER['api_base']}/admin/videos/direct-publish",
        data=json.dumps(video_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "X-Transcode-Key": MAIN_SERVER['transcode_key']
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        print(f"API响应: {result}")
        print(f"耗时: {time.time() - start:.1f}秒")
except urllib.error.HTTPError as e:
    print(f"HTTP错误: {e.code}")
    print(f"响应: {e.read().decode()}")
except Exception as e:
    print(f"API调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\\n测试完成!")
'''

# 上传并执行
sftp = ssh.open_sftp()
with sftp.file('D:/test_upload_step.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行分步测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\test_upload_step.py', timeout=600)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
