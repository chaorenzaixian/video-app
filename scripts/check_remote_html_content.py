"""检查远程HTML文件内容"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查远程HTML文件中的loadQueue函数
print('=== 检查远程index.html中的loadQueue函数 ===')
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\templates\index.html | Select-String -Pattern \"async function loadQueue|/api/queue|async function loadPending|/api/pending\""'
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stdout.read().decode('utf-8', errors='ignore')
print(output if output else '未找到匹配内容')

# 检查web_ui.py中的API定义
print('\n=== 检查远程web_ui.py中的API定义 ===')
cmd = r'powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py | Select-String -Pattern \"@app.route\(\x27/api/queue|@app.route\(\x27/api/pending|def get_queue|def get_pending\""'
stdin, stdout, stderr = ssh.exec_command(cmd)
output = stdout.read().decode('utf-8', errors='ignore')
print(output if output else '未找到匹配内容')

# 直接测试API
print('\n=== 直接测试API ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/queue')
queue_data = stdout.read().decode()
print(f'/api/queue 返回: {queue_data[:200]}...' if len(queue_data) > 200 else f'/api/queue 返回: {queue_data}')

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
pending_data = stdout.read().decode()
print(f'/api/pending 返回: {pending_data[:200]}...' if len(pending_data) > 200 else f'/api/pending 返回: {pending_data}')

ssh.close()
print('\n完成!')
