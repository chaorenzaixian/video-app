"""
检查待发布视频的HLS目录大小
"""
import paramiko

# 转码服务器
TRANSCODE_HOST = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASS = "jCkMIjNlnSd7f6GM"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)

# 获取第一个待发布任务的目录大小
task_id = "20260122033237306288"
cmd = f'powershell "(Get-ChildItem -Path D:\\VideoTranscode\\processing\\{task_id} -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"任务 {task_id} 总大小: {out.strip()} MB")

# 检查HLS目录
cmd = f'powershell "(Get-ChildItem -Path D:\\VideoTranscode\\processing\\{task_id}\\hls -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"HLS目录大小: {out.strip()} MB")

# 列出HLS文件
cmd = f'dir D:\\VideoTranscode\\processing\\{task_id}\\hls'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('gbk', errors='ignore')
print(f"\nHLS目录内容:\n{out}")

client.close()
