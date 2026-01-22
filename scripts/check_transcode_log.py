import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 检查nssm日志
stdin, stdout, stderr = c.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\service\\nssm_stderr.log -Tail 100"')
print("=== STDERR LOG ===")
print(stdout.read().decode('utf-8', errors='ignore'))

stdin, stdout, stderr = c.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\service\\nssm_stdout.log -Tail 100"')
print("=== STDOUT LOG ===")
print(stdout.read().decode('utf-8', errors='ignore'))

c.close()
