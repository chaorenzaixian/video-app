import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
sftp = ssh.open_sftp()
content = '''import urllib.request
import json

# Test /api/system
try:
    resp = urllib.request.urlopen('http://localhost:8080/api/system', timeout=5)
    print('/api/system:', resp.read().decode())
except Exception as e:
    print(f'/api/system Error: {e}')

# Test /api/delete-batch
try:
    data = json.dumps({'task_ids': ['test123']}).encode()
    req = urllib.request.Request('http://localhost:8080/api/delete-batch', data=data, headers={'Content-Type': 'application/json'}, method='POST')
    resp = urllib.request.urlopen(req, timeout=5)
    print('/api/delete-batch:', resp.read().decode())
except Exception as e:
    print(f'/api/delete-batch Error: {e}')

# Test /api/pending
try:
    resp = urllib.request.urlopen('http://localhost:8080/api/pending', timeout=5)
    data = json.loads(resp.read().decode())
    print(f'/api/pending: {len(data)} tasks')
except Exception as e:
    print(f'/api/pending Error: {e}')
'''
with sftp.file('D:/VideoTranscode/service/test_import.py', 'w') as f:
    f.write(content)
sftp.close()
stdin, stdout, stderr = ssh.exec_command('cd /d D:\\VideoTranscode\\service && python test_import.py')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
