"""
检查转码队列状态
"""
import paramiko
import json

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 检查队列
    print("转码队列:")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/queue')
    result = stdout.read().decode('utf-8', errors='ignore')
    data = json.loads(result) if result else {}
    
    tasks = data.get('tasks', [])
    print(f"共 {len(tasks)} 个任务")
    for t in tasks:
        print(f"  - ID:{t.get('id')} Status:{t.get('status')} File:{t.get('filename')}")
        print(f"    Path: {t.get('filepath')}")
    
    # 检查这些文件是否存在
    print("\n检查文件是否存在:")
    for t in tasks:
        filepath = t.get('filepath', '')
        if filepath:
            stdin, stdout, stderr = client.exec_command(f'if exist "{filepath}" (echo EXISTS) else (echo NOT_FOUND)')
            result = stdout.read().decode('gbk', errors='ignore').strip()
            print(f"  {t.get('filename')}: {result}")
    
    client.close()

if __name__ == '__main__':
    main()
