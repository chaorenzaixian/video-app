"""检查远程web_ui.py是否包含delete-batch"""
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

# 检查文件内容
cmd = 'findstr "delete-batch" D:\\VideoTranscode\\service\\web_ui.py'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"delete-batch in web_ui.py:\n{out}")

# 检查服务状态
cmd = 'tasklist | findstr python'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"\nPython processes:\n{out}")

# 测试API
cmd = 'curl -X POST http://localhost:8080/api/delete-batch -H "Content-Type: application/json" -d "{\\"task_ids\\":[]}" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
out = stdout.read().decode('utf-8', errors='ignore')
print(f"\nAPI test:\n{out}")

ssh.close()
