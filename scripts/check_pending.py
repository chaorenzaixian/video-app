"""
检查待发布任务
"""
import paramiko
import json

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 检查processing目录
    print("Processing目录内容:")
    stdin, stdout, stderr = client.exec_command('dir D:\\VideoTranscode\\processing /b')
    dirs = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
    print(f"  共 {len(dirs)} 个项目")
    
    for d in dirs[:5]:
        d = d.strip()
        if not d:
            continue
        print(f"\n  [{d}]")
        # 检查是否有hls和covers
        stdin, stdout, stderr = client.exec_command(f'dir "D:\\VideoTranscode\\processing\\{d}" /b')
        contents = stdout.read().decode('gbk', errors='ignore').strip()
        print(f"    内容: {contents[:100]}")
    
    # 检查API
    print("\n\nAPI状态:")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
    result = stdout.read().decode('utf-8', errors='ignore')
    data = json.loads(result) if result else {}
    print(f"  Pending任务数: {len(data.get('items', []))}")
    
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/queue')
    result = stdout.read().decode('utf-8', errors='ignore')
    data = json.loads(result) if result else {}
    print(f"  队列任务数: {len(data.get('tasks', []))}")
    
    # 测试一个具体任务
    if dirs:
        task_id = dirs[0].strip()
        if task_id:
            print(f"\n测试任务状态: {task_id}")
            stdin, stdout, stderr = client.exec_command(f'curl -s http://localhost:8080/api/status/{task_id}')
            result = stdout.read().decode('utf-8', errors='ignore')
            print(f"  结果: {result[:200]}")
    
    client.close()

if __name__ == '__main__':
    main()
