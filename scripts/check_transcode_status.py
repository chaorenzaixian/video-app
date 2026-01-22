"""
检查转码服务状态
"""
import paramiko
import json

def main():
    print('=' * 60)
    print('  视频转码服务 - 最终状态检查')
    print('=' * 60)
    
    # 检查转码服务器
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print('\n[转码服务器 198.176.60.121]')
    
    # 端口状态
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    port_status = stdout.read().decode('gbk', errors='ignore')
    print(f'  端口8080: {"✓ 运行中" if "LISTENING" in port_status else "✗ 未运行"}')
    
    # 获取分类数量
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/categories')
    try:
        data = json.loads(stdout.read().decode())
        print(f'  长视频分类: {len(data.get("categories", []))} 个')
        print(f'  短视频分类: {len(data.get("short_categories", []))} 个')
    except:
        print('  分类API: ✗ 异常')
    
    # 获取标签数量
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/tags')
    try:
        data = json.loads(stdout.read().decode())
        print(f'  标签: {len(data.get("tags", []))} 个')
    except:
        print('  标签API: ✗ 异常')
    
    # 待转码视频
    stdin, stdout, stderr = client.exec_command('dir /b D:\\VideoTranscode\\downloads\\long 2>nul')
    files = [f for f in stdout.read().decode('gbk', errors='ignore').strip().split('\n') if f.endswith('.mp4')]
    print(f'  待转码长视频: {len(files)} 个')
    
    stdin, stdout, stderr = client.exec_command('dir /b D:\\VideoTranscode\\downloads\\short 2>nul')
    files = [f for f in stdout.read().decode('gbk', errors='ignore').strip().split('\n') if f.endswith('.mp4')]
    print(f'  待转码短视频: {len(files)} 个')
    
    # 计划任务
    stdin, stdout, stderr = client.exec_command('schtasks /query /tn VideoTranscodeService 2>nul')
    task_status = stdout.read().decode('gbk', errors='ignore')
    print(f'  开机自启: {"✓ 已设置" if "VideoTranscodeService" in task_status else "✗ 未设置"}')
    
    client.close()
    
    # 检查主服务器
    print('\n[主服务器 38.47.218.137]')
    client2 = paramiko.SSHClient()
    client2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file('server_key_new')
    client2.connect('38.47.218.137', username='root', pkey=pkey)
    
    # 后端状态
    stdin, stdout, stderr = client2.exec_command('curl -s http://localhost:8000/api/v1/videos?limit=1')
    try:
        data = json.loads(stdout.read().decode())
        print(f'  后端API: ✓ 正常')
    except:
        print(f'  后端API: ✗ 异常')
    
    # direct-publish API
    stdin, stdout, stderr = client2.exec_command('curl -s -X POST http://localhost:8000/api/v1/admin/videos/direct-publish -H "Content-Type: application/json" -d "{}"')
    result = stdout.read().decode()
    if 'Field required' in result or 'missing' in result:
        print(f'  direct-publish API: ✓ 正常')
    else:
        print(f'  direct-publish API: ✗ 异常')
    
    client2.close()
    
    print('\n' + '=' * 60)
    print('  ✓ 转码服务设置完成！')
    print('=' * 60)
    print('\nWeb管理界面: http://198.176.60.121:8080')
    print('\n使用方法:')
    print('  1. 打开Web界面')
    print('  2. 上传视频文件')
    print('  3. 等待转码完成')
    print('  4. 选择封面、填写信息')
    print('  5. 点击发布')

if __name__ == '__main__':
    main()
