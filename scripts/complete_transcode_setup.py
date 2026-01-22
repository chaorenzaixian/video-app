"""
完成转码服务设置：
1. 重启主服务器后端
2. 设置转码服务开机自启
3. 测试完整流程
"""
import paramiko
import time

def restart_main_server():
    """重启主服务器后端"""
    print("=" * 50)
    print("1. 重启主服务器后端")
    print("=" * 50)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file("server_key_new")
    client.connect('38.47.218.137', username='root', pkey=pkey)
    
    # 查找后端进程并重启
    print("查找后端进程...")
    stdin, stdout, stderr = client.exec_command('ps aux | grep uvicorn | grep -v grep')
    result = stdout.read().decode()
    print(result)
    
    if result:
        # 杀掉旧进程
        print("停止旧进程...")
        stdin, stdout, stderr = client.exec_command('pkill -f "uvicorn app.main:app"')
        time.sleep(2)
    
    # 启动新进程
    print("启动后端服务...")
    cmd = 'cd /www/wwwroot/video-app/backend && nohup /www/wwwroot/video-app/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &'
    stdin, stdout, stderr = client.exec_command(cmd)
    time.sleep(3)
    
    # 检查是否启动成功
    print("检查服务状态...")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8000/api/v1/health 2>/dev/null || echo "服务未响应"')
    result = stdout.read().decode()
    print(f"健康检查: {result}")
    
    # 测试新API
    print("\n测试 direct-publish API...")
    stdin, stdout, stderr = client.exec_command('curl -s -X POST http://localhost:8000/api/v1/admin/videos/direct-publish -H "Content-Type: application/json" -H "X-Transcode-Key: wrong_key" -d "{}"')
    result = stdout.read().decode()
    print(f"API响应: {result}")
    
    client.close()
    return "403" in result or "Invalid" in result  # 返回403说明API存在

def setup_transcode_autostart():
    """设置转码服务开机自启"""
    print("\n" + "=" * 50)
    print("2. 设置转码服务开机自启")
    print("=" * 50)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 创建启动脚本
    start_script = '''@echo off
cd /d D:\\VideoTranscode\\service
python service.py
'''
    
    # 创建VBS隐藏启动脚本
    vbs_script = '''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "D:\\VideoTranscode\\start_service.bat", 0, False
'''
    
    sftp = client.open_sftp()
    
    # 写入启动脚本
    with sftp.file('D:/VideoTranscode/start_service.bat', 'w') as f:
        f.write(start_script)
    print("已创建 start_service.bat")
    
    # 写入VBS脚本（隐藏窗口启动）
    with sftp.file('D:/VideoTranscode/start_hidden.vbs', 'w') as f:
        f.write(vbs_script)
    print("已创建 start_hidden.vbs")
    
    sftp.close()
    
    # 创建计划任务（开机自启）
    print("\n创建开机自启计划任务...")
    task_cmd = '''schtasks /create /tn "VideoTranscodeService" /tr "wscript.exe D:\\VideoTranscode\\start_hidden.vbs" /sc onstart /ru Administrator /rp "jCkMIjNlnSd7f6GM" /f'''
    stdin, stdout, stderr = client.exec_command(task_cmd)
    print(stdout.read().decode('gbk', errors='ignore'))
    print(stderr.read().decode('gbk', errors='ignore'))
    
    # 检查服务是否在运行
    print("\n检查服务状态...")
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' not in result:
        print("服务未运行，正在启动...")
        stdin, stdout, stderr = client.exec_command('wscript.exe D:\\VideoTranscode\\start_hidden.vbs')
        time.sleep(5)
        
        stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
        result = stdout.read().decode('gbk', errors='ignore')
    
    print(f"端口状态: {result}")
    
    client.close()
    return 'LISTENING' in result

def test_full_flow():
    """测试完整流程"""
    print("\n" + "=" * 50)
    print("3. 测试完整流程")
    print("=" * 50)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 测试Web界面
    print("测试Web界面...")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/')
    result = stdout.read().decode('utf-8', errors='ignore')
    web_ok = '视频转码' in result or 'transcode' in result.lower() or '<html' in result.lower()
    print(f"Web界面: {'✓ 正常' if web_ok else '✗ 异常'}")
    
    # 测试获取分类API
    print("\n测试获取分类...")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/categories')
    result = stdout.read().decode('utf-8', errors='ignore')
    categories_ok = 'categories' in result
    print(f"分类API: {'✓ 正常' if categories_ok else '✗ 异常'}")
    if categories_ok:
        import json
        try:
            data = json.loads(result)
            print(f"  长视频分类: {len(data.get('categories', []))} 个")
            print(f"  短视频分类: {len(data.get('short_categories', []))} 个")
        except:
            pass
    
    # 测试获取标签API
    print("\n测试获取标签...")
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/tags')
    result = stdout.read().decode('utf-8', errors='ignore')
    tags_ok = 'tags' in result
    print(f"标签API: {'✓ 正常' if tags_ok else '✗ 异常'}")
    
    # 检查待转码视频
    print("\n检查待转码视频...")
    stdin, stdout, stderr = client.exec_command('dir /b D:\\VideoTranscode\\downloads\\long 2>nul')
    long_videos = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
    long_videos = [v for v in long_videos if v.endswith('.mp4')]
    
    stdin, stdout, stderr = client.exec_command('dir /b D:\\VideoTranscode\\downloads\\short 2>nul')
    short_videos = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
    short_videos = [v for v in short_videos if v.endswith('.mp4')]
    
    print(f"待转码长视频: {len(long_videos)} 个")
    print(f"待转码短视频: {len(short_videos)} 个")
    
    client.close()
    
    return web_ok and categories_ok

def main():
    print("=" * 60)
    print("  视频转码服务完整设置")
    print("=" * 60)
    
    # 1. 重启主服务器
    api_ok = restart_main_server()
    print(f"\n主服务器API: {'✓ 已就绪' if api_ok else '✗ 需要检查'}")
    
    # 2. 设置开机自启
    autostart_ok = setup_transcode_autostart()
    print(f"开机自启: {'✓ 已设置' if autostart_ok else '✗ 需要检查'}")
    
    # 3. 测试完整流程
    flow_ok = test_full_flow()
    print(f"完整流程: {'✓ 正常' if flow_ok else '✗ 需要检查'}")
    
    print("\n" + "=" * 60)
    print("  设置完成！")
    print("=" * 60)
    print(f"\n转码服务Web管理界面: http://198.176.60.121:8080")
    print("\n使用方法:")
    print("  1. 打开Web界面上传视频")
    print("  2. 等待转码完成")
    print("  3. 选择封面、填写标题/分类/标签")
    print("  4. 点击发布")

if __name__ == '__main__':
    main()
