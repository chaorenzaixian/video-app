"""完整API测试"""
import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

print('=' * 60)
print('转码管理页面 API 完整测试')
print('页面地址: http://198.176.60.121:8080')
print('=' * 60)

# 1. 首页
print('\n1. 首页 (/)')
stdin, stdout, stderr = ssh.exec_command('curl -s -w "\\nHTTP_CODE:%{http_code}" http://localhost:8080/')
output = stdout.read().decode('utf-8', errors='ignore')
if 'HTTP_CODE:200' in output:
    print('   ✓ 首页可访问 (HTTP 200)')
    if '转码管理' in output or 'video' in output.lower():
        print('   ✓ 页面内容正常')
else:
    print('   ✗ 首页访问失败')

# 2. 系统信息
print('\n2. 系统信息 (/api/system)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/system')
data = json.loads(stdout.read().decode())
print(f'   磁盘可用: {data.get("disk_free_gb", 0)} GB')
print(f'   待发布数: {data.get("pending_count", 0)}')

# 3. 转码队列
print('\n3. 转码队列 (/api/queue)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/queue')
data = json.loads(stdout.read().decode())
print(f'   正在转码: {len(data)} 个任务')
if data:
    for t in data[:3]:
        print(f'   - {t.get("filename", "")[:30]}... status={t.get("status")}')

# 4. 待发布列表
print('\n4. 待发布列表 (/api/pending)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/pending')
data = json.loads(stdout.read().decode())
print(f'   待发布: {len(data)} 个任务')
ready_count = len([t for t in data if t.get('status') == 'ready'])
scheduled_count = len([t for t in data if t.get('status') == 'scheduled'])
print(f'   - ready状态: {ready_count}')
print(f'   - scheduled状态: {scheduled_count}')
if data:
    for t in data[:3]:
        print(f'   - {t.get("filename", "")[:30]}... status={t.get("status")}')

# 5. 发布历史
print('\n5. 发布历史 (/api/history)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/history')
data = json.loads(stdout.read().decode())
items = data.get('items', []) if isinstance(data, dict) else data
stats = data.get('stats', {}) if isinstance(data, dict) else {}
print(f'   总计: {stats.get("total", len(items))}')
print(f'   今日: {stats.get("today", 0)}')
if items:
    for h in items[:3]:
        print(f'   - {h.get("title", h.get("filename", ""))[:30]}...')

# 6. 分类
print('\n6. 分类 (/api/categories)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/categories')
data = json.loads(stdout.read().decode())
print(f'   长视频分类: {len(data.get("video_categories", []))}')
print(f'   短视频分类: {len(data.get("short_categories", []))}')
print(f'   暗网分类: {len(data.get("darkweb_categories", []))}')

# 7. 标签
print('\n7. 标签 (/api/tags)')
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8080/api/tags')
data = json.loads(stdout.read().decode())
print(f'   普通标签: {len(data.get("tags", []))}')
print(f'   暗网标签: {len(data.get("darkweb_tags", []))}')

print('\n' + '=' * 60)
print('测试完成!')
print('请在浏览器中访问: http://198.176.60.121:8080')
print('如果页面显示不正确，请按 Ctrl+F5 强制刷新')
print('=' * 60)

ssh.close()
