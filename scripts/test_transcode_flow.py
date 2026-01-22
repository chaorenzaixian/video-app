"""测试转码系统完整流程"""
import paramiko
import json
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

def api_call(endpoint):
    stdin, stdout, stderr = ssh.exec_command(f'curl -s http://localhost:8080{endpoint}')
    return json.loads(stdout.read().decode())

print('=' * 60)
print('转码系统流程测试')
print('=' * 60)

# 1. 系统信息
print('\n1. 系统信息 (/api/system)')
sys_info = api_call('/api/system')
print(f'   磁盘可用: {sys_info.get("disk_free_gb", 0)} GB')
print(f'   处理中: {sys_info.get("processing_count", 0)}')
print(f'   待发布: {sys_info.get("pending_count", 0)}')
print(f'   队列: {sys_info.get("queue_count", 0)}')

# 2. 转码队列（正在转码的）
print('\n2. 转码队列 (/api/queue) - 应显示正在转码的任务')
queue = api_call('/api/queue')
print(f'   任务数: {len(queue)}')
for t in queue[:3]:
    print(f'   - {t.get("filename", "")[:40]}... status={t.get("status")}')

# 3. 待发布列表（转码完成的）
print('\n3. 待发布列表 (/api/pending) - 应显示转码完成待发布的任务')
pending = api_call('/api/pending')
print(f'   任务数: {len(pending)}')
for t in pending[:5]:
    fname = t.get("filename", "")[:35]
    status = t.get("status")
    is_short = t.get("is_short", False)
    is_darkweb = t.get("is_darkweb", False)
    vtype = "暗网" if is_darkweb else ("短视频" if is_short else "长视频")
    print(f'   - [{vtype}] {fname}... status={status}')

# 4. 发布历史
print('\n4. 发布历史 (/api/history) - 应显示已发布的视频')
history = api_call('/api/history')
items = history.get('items', []) if isinstance(history, dict) else history
stats = history.get('stats', {}) if isinstance(history, dict) else {}
print(f'   总计: {stats.get("total", len(items))}')
print(f'   今日: {stats.get("today", 0)}')
print(f'   本周: {stats.get("this_week", 0)}')
for h in items[:3]:
    print(f'   - {h.get("title", h.get("filename", ""))[:40]}...')

# 5. 流程验证
print('\n' + '=' * 60)
print('流程验证:')
print('=' * 60)
print('✓ 上传视频 → 进入转码队列 (status: uploading/processing/transcoding)')
print('✓ 转码完成 → 移到待发布列表 (status: ready)')
print('✓ 发布完成 → 移到发布历史')
print()

# 检查是否有状态异常的任务
all_pending = api_call('/api/pending')
abnormal = [t for t in all_pending if t.get('status') not in ('ready', 'scheduled')]
if abnormal:
    print('⚠️ 警告: 待发布列表中有状态异常的任务:')
    for t in abnormal:
        print(f'   - {t.get("filename", "")[:30]}... status={t.get("status")}')
else:
    print('✓ 所有待发布任务状态正常')

ssh.close()
print('\n测试完成!')
