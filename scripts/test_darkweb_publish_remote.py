"""从转码服务器内部测试暗网视频发布"""
import paramiko
import json
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
test_script = '''
import urllib.request
import json

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

url = "http://localhost:8080/api/publish-darkweb"
print(f"POST {url}")

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
'''

# 写入测试脚本
sftp = client.open_sftp()
with sftp.file('D:/VideoTranscode/test_publish.py', 'w') as f:
    f.write(test_script)
sftp.close()

# 执行测试
print("Running test...")
stdin, stdout, stderr = client.exec_command('python D:\\VideoTranscode\\test_publish.py', timeout=180)
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(f"Output: {result}")
if error:
    print(f"Stderr: {error}")

client.close()
