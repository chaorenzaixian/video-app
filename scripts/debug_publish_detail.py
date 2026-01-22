"""
详细查看发布状态
"""
import urllib.request
import json
import paramiko

# 1. 获取转码队列
print("=== 1. 转码队列详情 ===")
r = urllib.request.urlopen('http://198.176.60.121:8080/api/queue', timeout=10)
queue = json.loads(r.read().decode())

publishing = [i for i in queue if i.get('status') == 'publishing']
print(f"正在发布: {len(publishing)}")

for item in publishing[:5]:
    print(f"\n  任务ID: {item.get('task_id')}")
    print(f"  文件名: {item.get('filename')}")
    print(f"  类型: {'短视频' if item.get('is_short') else '长视频'}")
    print(f"  状态: {item.get('status')}")
    print(f"  进度: {item.get('publish_progress')}")
    if item.get('publish_error'):
        print(f"  错误: {item.get('publish_error')}")

# 2. 连接转码服务器检查日志
print("\n\n=== 2. 检查转码服务器进程 ===")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

# 检查Python进程
cmd = 'tasklist /FI "IMAGENAME eq python.exe"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
print(stdout.read().decode('gbk', errors='ignore'))

# 检查网络连接到主服务器
print("\n=== 3. 检查到主服务器的连接 ===")
cmd = 'netstat -an | findstr "38.47.218.137"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('gbk', errors='ignore')
if output.strip():
    lines = output.strip().split('\n')
    print(f"到主服务器的连接数: {len(lines)}")
    for line in lines[:10]:
        print(f"  {line.strip()}")
else:
    print("没有到主服务器的连接!")

# 测试SSH连接
print("\n=== 4. 测试SSH连接到主服务器 ===")
test_cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@38.47.218.137 "echo OK" 2>&1'
stdin, stdout, stderr = client.exec_command(test_cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print(f"结果: {out.strip()}")
if err:
    print(f"错误: {err.strip()}")

client.close()
