"""测试真实发布流程"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 获取一个有封面的待发布任务
print('=== 获取待发布任务 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
pending = json.loads(stdout.read().decode())

if not pending:
    print('没有待发布任务')
    exit()

# 选择一个有封面的任务
task = pending[0]
task_id = task.get('task_id')
print(f'任务ID: {task_id}')
print(f'文件名: {task.get("filename")}')
print(f'封面数: {len(task.get("covers", []))}')
print(f'is_short: {task.get("is_short")}')
print(f'is_darkweb: {task.get("is_darkweb")}')

# 发布数据
publish_data = {
    "task_id": task_id,
    "title": task.get('name', 'Test Video'),
    "description": "测试发布",
    "selected_cover": task.get('best_cover', 5),
    "is_vip_only": False,
    "is_featured": False,
    "coin_price": 0,
    "free_preview_seconds": 15
}

print(f'\n=== 发送发布请求 ===')
print(f'数据: {json.dumps(publish_data, ensure_ascii=False)}')

# 使用curl发送POST请求
import subprocess
curl_cmd = f'''curl -s -X POST "http://localhost:8080/api/publish" -H "Content-Type: application/json" -d '{json.dumps(publish_data)}' --max-time 300'''

print(f'\n执行: {curl_cmd[:100]}...')

stdin, stdout, stderr = ssh.exec_command(curl_cmd, timeout=300)
result = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(f'\n响应: {result}')
if error:
    print(f'错误: {error}')

# 检查发布历史
print('\n=== 检查发布历史 ===')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
history = json.loads(stdout.read().decode())
items = history.get('items', []) if isinstance(history, dict) else history
print(f'发布历史数: {len(items)}')
if items:
    for h in items[:3]:
        print(f'  - {h.get("title", h.get("filename", ""))[:40]}')

ssh.close()
