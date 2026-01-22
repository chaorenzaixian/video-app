"""
更新转码服务器上的服务文件
"""
import paramiko
import os

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 要上传的文件
    files = [
        'transcode_service/config.py',
        'transcode_service/service.py',
        'transcode_service/web_ui.py',
        'transcode_service/worker.py',
        'transcode_service/transcoder.py',
        'transcode_service/uploader.py',
        'transcode_service/task_queue.py',
        'transcode_service/callback.py',
        'transcode_service/templates/index.html',
    ]
    
    remote_base = 'D:/VideoTranscode/service'
    
    for local_file in files:
        if not os.path.exists(local_file):
            print(f"跳过不存在的文件: {local_file}")
            continue
            
        # 读取本地文件
        with open(local_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 确定远程路径
        filename = local_file.replace('transcode_service/', '')
        remote_path = f"{remote_base}/{filename}"
        
        # 确保目录存在
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except:
            sftp.mkdir(remote_dir)
        
        # 上传文件
        with sftp.file(remote_path, 'w') as f:
            f.write(content)
        print(f"已上传: {remote_path}")
    
    sftp.close()
    
    # 重启服务
    print("\n重启服务...")
    
    # 先停止
    stdin, stdout, stderr = client.exec_command('taskkill /f /im python.exe 2>nul')
    import time
    time.sleep(2)
    
    # 启动
    stdin, stdout, stderr = client.exec_command('wscript.exe D:\\VideoTranscode\\start_hidden.vbs')
    time.sleep(5)
    
    # 检查
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    
    if 'LISTENING' in result:
        print("✓ 服务已重启")
    else:
        print("✗ 服务启动失败")
    
    client.close()
    print("\n完成！Web界面: http://198.176.60.121:8080")

if __name__ == '__main__':
    main()
