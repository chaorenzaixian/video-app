"""
用二进制模式上传文件
"""
import paramiko
import os

def main():
    print("连接转码服务器...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 上传web_ui.py
    local_file = 'transcode_service/web_ui.py'
    remote_file = 'D:/VideoTranscode/service/web_ui.py'
    
    print(f"上传 {local_file}...")
    
    # 读取本地文件
    with open(local_file, 'rb') as f:
        content = f.read()
    
    print(f"本地文件大小: {len(content)} 字节")
    
    # 检查是否有recover函数
    if b'recover_pending_tasks' in content:
        print("✓ 本地文件包含recover_pending_tasks")
    
    # 用put方法上传
    sftp.put(local_file, remote_file)
    
    # 验证
    with sftp.file(remote_file, 'rb') as f:
        remote_content = f.read()
    
    print(f"远程文件大小: {len(remote_content)} 字节")
    
    if b'recover_pending_tasks' in remote_content:
        print("✓ 远程文件包含recover_pending_tasks")
    else:
        print("✗ 远程文件不包含recover_pending_tasks")
    
    # 上传其他文件
    files = [
        'transcode_service/config.py',
        'transcode_service/uploader.py',
        'transcode_service/task_queue.py',
        'transcode_service/templates/index.html',
    ]
    
    for f in files:
        if os.path.exists(f):
            remote = f'D:/VideoTranscode/service/{f.replace("transcode_service/", "")}'
            sftp.put(f, remote)
            print(f"✓ {f}")
    
    sftp.close()
    
    # 重启服务
    print("\n重启服务...")
    import time
    
    # 先杀掉所有python进程
    client.exec_command('taskkill /f /im python.exe 2>nul')
    time.sleep(3)
    
    # 直接用wmic启动进程（更可靠）
    cmd = 'wmic process call create "cmd /c cd /d D:\\VideoTranscode\\service && python web_ui.py"'
    stdin, stdout, stderr = client.exec_command(cmd)
    time.sleep(5)
    
    # 多等几秒确保服务启动
    for i in range(5):
        stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
        result = stdout.read().decode('gbk', errors='ignore')
        if 'LISTENING' in result:
            break
        print(f"  等待服务启动... ({i+1}/5)")
        time.sleep(2)
    
    # 检查
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr ":8080" | findstr "LISTENING"')
    result = stdout.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in result:
        print("✓ 服务已启动")
        
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
        pending = stdout.read().decode('utf-8', errors='ignore')
        print(f"Pending: {pending[:300]}")
    else:
        print("✗ 服务启动失败")
    
    client.close()
    print("\n完成!")

if __name__ == '__main__':
    main()
