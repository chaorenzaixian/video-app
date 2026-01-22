"""详细测试发布流程"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')

from config import DIRS, MAIN_SERVER
from uploader import Uploader
from task_queue import TaskQueue
import json
import os

print("=== 测试发布流程 ===")

# 获取一个待发布任务
processing_dir = DIRS["processing"]
task_dirs = [d for d in os.listdir(processing_dir) if os.path.isdir(os.path.join(processing_dir, d))]

if not task_dirs:
    print("没有待发布任务")
    sys.exit(0)

task_id = task_dirs[0]
task_path = os.path.join(processing_dir, task_id)
print(f"测试任务: {task_id}")

# 检查HLS目录
hls_dir = os.path.join(task_path, "hls")
if os.path.exists(hls_dir):
    files = os.listdir(hls_dir)
    print(f"HLS目录存在, 文件数: {len(files)}")
    print(f"  文件: {files[:5]}...")
else:
    print("HLS目录不存在!")

# 检查封面目录
covers_dir = os.path.join(task_path, "covers")
if os.path.exists(covers_dir):
    files = os.listdir(covers_dir)
    print(f"封面目录存在, 文件数: {len(files)}")
else:
    print("封面目录不存在!")

# 测试上传
print("\\n=== 测试上传 ===")
uploader = Uploader()

# 测试SSH连接
print("测试SSH连接...")
if uploader._connect():
    print("SSH连接成功!")
else:
    print("SSH连接失败!")
    sys.exit(1)

# 测试上传HLS
print("\\n测试上传HLS...")
video_id = f"test_{task_id[:8]}"
try:
    hls_url = uploader.upload_hls(hls_dir, video_id)
    print(f"HLS上传结果: {hls_url}")
except Exception as e:
    print(f"HLS上传失败: {e}")
    import traceback
    traceback.print_exc()

# 测试上传封面
print("\\n测试上传封面...")
try:
    covers_url = uploader.upload_covers(covers_dir, video_id)
    print(f"封面上传结果: {covers_url}")
except Exception as e:
    print(f"封面上传失败: {e}")
    import traceback
    traceback.print_exc()

print("\\n测试完成!")
'''

# 上传并执行
sftp = ssh.open_sftp()
with sftp.file('D:/test_publish.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试脚本...')
stdin, stdout, stderr = ssh.exec_command('python D:\\test_publish.py', timeout=120)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
