import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 添加防火墙规则
cmd = 'netsh advfirewall firewall add rule name="Transcode8080" dir=in action=allow protocol=tcp localport=8080'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Add rule:', stdout.read().decode('gbk', errors='ignore'), stderr.read().decode('gbk', errors='ignore'))

# 验证
stdin, stdout, stderr = ssh.exec_command('netsh advfirewall firewall show rule name="Transcode8080"')
print('Verify:', stdout.read().decode('gbk', errors='ignore'))

ssh.close()
