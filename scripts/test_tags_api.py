"""测试标签API"""
import paramiko

host = "198.176.60.121"
user = "Administrator"
password = "jCkMIjNlnSd7f6GM"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password)

# 测试标签API
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/tags')
tags = stdout.read().decode()
print("标签API响应:", tags[:500] if tags else "无")

# 测试分类API
stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:8080/api/categories')
cats = stdout.read().decode()
print("\n分类API响应:", cats[:500] if cats else "无")

# 检查index.html是否有标签功能
stdin, stdout, stderr = ssh.exec_command('findstr "tagsContainer" D:\\VideoTranscode\\service\\templates\\index.html')
tags_html = stdout.read().decode().strip()
print("\n标签HTML:", "已添加" if tags_html else "未添加")

stdin, stdout, stderr = ssh.exec_command('findstr "loadTags" D:\\VideoTranscode\\service\\templates\\index.html')
load_tags = stdout.read().decode().strip()
print("loadTags函数:", "已添加" if load_tags else "未添加")

ssh.close()
