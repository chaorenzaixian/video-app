"""
重启转码服务并检查状态
"""
import paramiko
import time
import urllib.request
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

# 1. 停止当前服务
print("1. 停止当前服务...")
cmd = 'taskkill /F /IM python.exe 2>nul'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
time.sleep(2)

# 2. 重启服务
print("2. 重启服务...")
cmd = 'powershell -Command "Start-Process python -ArgumentList \'D:\\VideoTranscode\\service\\web_ui.py\' -WorkingDirectory \'D:\\VideoTranscode\\service\' -WindowStyle Hidden"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
time.sleep(3)

# 3. 检查服务是否启动
print("3. 检查服务状态...")
try:
    r = urllib.request.urlopen('http://198.176.60.121:8080/api/system', timeout=10)
    data = json.loads(r.read().decode())
    print(f"   服务已启动: {data}")
except Exception as e:
    print(f"   服务未启动: {e}")

# 4. 检查队列状态
print("\n4. 检查队列状态...")
try:
    r = urllib.request.urlopen('http://198.176.60.121:8080/api/queue', timeout=10)
    queue = json.loads(r.read().decode())
    publishing = [i for i in queue if i.get('status') == 'publishing']
    print(f"   正在发布: {len(publishing)}")
    
    r = urllib.request.urlopen('http://198.176.60.121:8080/api/pending', timeout=10)
    pending = json.loads(r.read().decode())
    print(f"   待发布: {len(pending)}")
except Exception as e:
    print(f"   错误: {e}")

client.close()
print("\n完成")
