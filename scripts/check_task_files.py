"""
检查任务文件是否存在
"""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

task_id = "20260122033237309468"
print(f"检查任务: {task_id}")

# 检查任务目录
cmd = f'dir D:\\VideoTranscode\\processing\\{task_id}'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('gbk', errors='ignore')
err = stderr.read().decode('gbk', errors='ignore')

if '找不到' in err or '找不到' in out:
    print(f"任务目录不存在!")
else:
    print(f"任务目录内容:\n{out}")

# 检查HLS目录
cmd = f'dir D:\\VideoTranscode\\processing\\{task_id}\\hls'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('gbk', errors='ignore')
if out.strip():
    print(f"\nHLS目录:\n{out}")

client.close()
