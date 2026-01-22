import paramiko
import json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 获取pending数据的详细信息
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
data = json.loads(stdout.read().decode())
print(f'Total pending: {len(data)}')

# 统计类型
long_count = len([t for t in data if not t.get('is_short') and not t.get('is_darkweb')])
short_count = len([t for t in data if t.get('is_short') and not t.get('is_darkweb')])
darkweb_count = len([t for t in data if t.get('is_darkweb')])
print(f'Long: {long_count}, Short: {short_count}, Darkweb: {darkweb_count}')

# 检查每个item
for i, item in enumerate(data[:3]):
    print(f'\nItem {i+1}:')
    print(f'  filename: {item.get("filename")}')
    print(f'  duration: {item.get("duration")}s')
    print(f'  is_short: {item.get("is_short")}')
    print(f'  is_darkweb: {item.get("is_darkweb")}')
    print(f'  status: {item.get("status")}')
    print(f'  covers count: {len(item.get("covers", []))}')

ssh.close()
