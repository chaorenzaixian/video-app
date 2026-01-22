"""检查远程服务器上的API代码"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)

# 检查get_queue和get_pending函数
print("=== 检查远程服务器上的get_queue函数 ===")
cmd = r'''powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py -Raw | Select-String -Pattern 'def get_queue\(\):[\s\S]*?return jsonify' -AllMatches | ForEach-Object { $_.Matches.Value }"'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

print("\n=== 检查远程服务器上的get_pending函数 ===")
cmd = r'''powershell -Command "Get-Content D:\VideoTranscode\service\web_ui.py -Raw | Select-String -Pattern 'def get_pending\(\):[\s\S]*?return jsonify' -AllMatches | ForEach-Object { $_.Matches.Value }"'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='ignore'))
print(stderr.read().decode('utf-8', errors='ignore'))

ssh.close()
