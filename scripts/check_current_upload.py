"""
检查当前正在上传的文件
"""
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

# 检查主服务器上最近修改的文件
print("=== 检查主服务器上最近上传的文件 ===")
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "find /www/wwwroot/video-app/backend/uploads/hls -type f -mmin -5 2>/dev/null | head -20"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
out = stdout.read().decode('utf-8', errors='ignore')
if out.strip():
    print("最近5分钟上传的文件:")
    for line in out.strip().split('\n')[:20]:
        print(f"  {line}")
else:
    print("最近5分钟没有新文件上传!")

# 检查主服务器上的hls目录
print("\n=== 检查主服务器HLS目录 ===")
cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -lt /www/wwwroot/video-app/backend/uploads/hls/ | head -10"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
print(stdout.read().decode('utf-8', errors='ignore'))

client.close()
