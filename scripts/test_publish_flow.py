"""测试发布流程"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 获取一个待发布任务
print('=== 获取待发布任务 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
pending = json.loads(stdout.read().decode())
print(f'待发布任务数: {len(pending)}')

if pending:
    task = pending[0]
    task_id = task.get('task_id')
    filename = task.get('filename', '')[:40]
    print(f'测试任务: {task_id}')
    print(f'文件名: {filename}')
    print(f'状态: {task.get("status")}')
    print(f'is_short: {task.get("is_short")}')
    print(f'is_darkweb: {task.get("is_darkweb")}')
    
    # 模拟发布请求
    print('\n=== 模拟发布请求 ===')
    publish_data = {
        "task_id": task_id,
        "title": task.get('name', 'Test'),
        "description": "",
        "selected_cover": task.get('best_cover', 5),
        "is_vip_only": False,
        "is_featured": False,
        "coin_price": 0,
        "free_preview_seconds": 15
    }
    print(f'发布数据: {json.dumps(publish_data, ensure_ascii=False)[:200]}...')
    
    # 发送发布请求
    cmd = f'''curl -s -X POST http://localhost:8080/api/publish -H "Content-Type: application/json" -d "{json.dumps(publish_data).replace('"', '\\"')}"'''
    print(f'\n执行命令...')
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read().decode()
    error = stderr.read().decode()
    print(f'响应: {result}')
    if error:
        print(f'错误: {error}')

# 检查发布历史
print('\n=== 检查发布历史 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
history = json.loads(stdout.read().decode())
items = history.get('items', []) if isinstance(history, dict) else history
print(f'发布历史数: {len(items)}')

ssh.close()
