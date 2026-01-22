"""
测试发布功能
"""
import paramiko
import json
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 获取pending任务
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
    result = stdout.read().decode('utf-8', errors='ignore')
    print('Pending任务:')
    data = json.loads(result)
    for item in data.get('items', []):
        print(f"  - {item['task_id']}: {item.get('filename', 'unknown')}")
    
    # 测试SSH连接到主服务器
    print('\n测试SSH连接到主服务器...')
    stdin, stdout, stderr = client.exec_command('ssh -i D:\\VideoTranscode\\server_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.47.218.137 "echo ok"')
    time.sleep(8)
    result = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print('结果:', result.strip() if result.strip() else '无')
    print('错误:', err.strip() if err.strip() else '无')
    
    client.close()

if __name__ == '__main__':
    main()
