"""
检查转码服务的线程状态
"""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("198.176.60.121", username="Administrator", password="jCkMIjNlnSd7f6GM", timeout=30)

# 检查Python进程的线程
print("=== 检查Python进程线程 ===")
cmd = 'powershell "Get-Process python | Select-Object Id, Threads | Format-List"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))

# 检查Flask服务的输出
print("\n=== 检查服务输出 ===")
# 尝试获取最近的控制台输出
cmd = 'powershell "Get-EventLog -LogName Application -Newest 10 -Source Python 2>$null"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
if out.strip():
    print(out)
else:
    print("没有Python事件日志")

# 检查是否有多个SSH连接尝试
print("\n=== 检查SSH连接历史 ===")
cmd = 'netstat -an | findstr ":22"'
stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
output = stdout.read().decode('gbk', errors='ignore')
lines = [l for l in output.strip().split('\n') if '38.47.218.137' in l]
print(f"到主服务器22端口的连接: {len(lines)}")
for line in lines:
    print(f"  {line.strip()}")

# 检查TIME_WAIT连接
time_wait = [l for l in lines if 'TIME_WAIT' in l]
established = [l for l in lines if 'ESTABLISHED' in l]
print(f"\nESTABLISHED: {len(established)}")
print(f"TIME_WAIT: {len(time_wait)}")

client.close()
