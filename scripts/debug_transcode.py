"""
深入调试转码服务启动问题
"""
import paramiko
import time

def main():
    print("连接转码服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 检查Python
    print("\n1. 检查Python...")
    stdin, stdout, stderr = client.exec_command('where python')
    print(f"Python路径: {stdout.read().decode('gbk', errors='ignore').strip()}")
    
    # 检查文件是否存在
    print("\n2. 检查服务文件...")
    stdin, stdout, stderr = client.exec_command('dir D:\\VideoTranscode\\service\\*.py /b')
    print(f"服务文件: {stdout.read().decode('gbk', errors='ignore')}")
    
    # 测试导入各个模块
    print("\n3. 测试导入模块...")
    modules = ['config', 'task_queue', 'transcoder', 'uploader', 'web_ui']
    for mod in modules:
        stdin, stdout, stderr = client.exec_command(
            f'cd /d D:\\VideoTranscode\\service && python -c "import {mod}; print(\'OK\')"'
        )
        time.sleep(2)
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        status = "✓" if out == "OK" else "✗"
        print(f"  {status} {mod}: {out if out else err[:100]}")
    
    # 直接运行web_ui看输出
    print("\n4. 直接运行web_ui (5秒)...")
    stdin, stdout, stderr = client.exec_command(
        'cd /d D:\\VideoTranscode\\service && python web_ui.py'
    )
    time.sleep(5)
    
    # 检查是否启动了
    stdin2, stdout2, stderr2 = client.exec_command('netstat -an | findstr ":8080"')
    port_result = stdout2.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in port_result:
        print("✓ 服务已启动!")
        stdin3, stdout3, stderr3 = client.exec_command('curl -s http://localhost:8080/api/pending')
        print(f"Pending: {stdout3.read().decode('utf-8', errors='ignore')[:300]}")
    else:
        print("✗ 服务未启动")
        print(f"端口状态: {port_result}")
    
    client.close()
    print("\n完成!")

if __name__ == '__main__':
    main()
