"""
测试从转码服务器到主服务器的SSH连接
"""
import paramiko
import io

def main():
    # 连接转码服务器
    print('连接转码服务器...')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    print('已连接转码服务器')
    
    # 获取密钥内容
    sftp = client.open_sftp()
    with sftp.file('D:/VideoTranscode/server_key', 'r') as f:
        key_content = f.read()
    sftp.close()
    print('已读取密钥文件')
    
    # 直接从本地测试连接主服务器
    print('\n直接测试连接主服务器...')
    main_client = paramiko.SSHClient()
    main_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 使用本地密钥
        main_client.connect('38.47.218.137', username='root', key_filename='server_key_new', timeout=10)
        stdin, stdout, stderr = main_client.exec_command('echo ok')
        result = stdout.read().decode()
        print('主服务器连接成功:', result.strip())
        main_client.close()
    except Exception as e:
        print('主服务器连接失败:', e)
    
    # 检查pending任务
    print('\n检查pending任务...')
    stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/pending')
    result = stdout.read().decode('utf-8', errors='ignore')
    print('Pending:', result[:500])
    
    client.close()

if __name__ == '__main__':
    main()
