"""
调试转码服务启动问题
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print("=== 检查服务目录 ===")
    stdin, stdout, stderr = client.exec_command('dir D:\\VideoTranscode\\service')
    print(stdout.read().decode('gbk', errors='ignore'))
    
    print("\n=== 检查Python版本 ===")
    stdin, stdout, stderr = client.exec_command('python --version')
    print(stdout.read().decode('gbk', errors='ignore'))
    print(stderr.read().decode('gbk', errors='ignore'))
    
    print("\n=== 检查Flask是否安装 ===")
    stdin, stdout, stderr = client.exec_command('pip show flask')
    print(stdout.read().decode('gbk', errors='ignore'))
    err = stderr.read().decode('gbk', errors='ignore')
    if err: print(f"Error: {err}")
    
    print("\n=== 尝试导入模块 ===")
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python -c "from config import SERVICE; print(SERVICE)"')
    print(stdout.read().decode('gbk', errors='ignore'))
    err = stderr.read().decode('gbk', errors='ignore')
    if err: print(f"Error: {err}")
    
    print("\n=== 尝试启动服务（5秒后停止）===")
    # 使用非阻塞方式启动
    stdin, stdout, stderr = client.exec_command('cd /d D:\\VideoTranscode\\service && python service.py 2>&1', timeout=10)
    
    # 等待几秒看输出
    time.sleep(5)
    
    # 检查是否有输出
    if stdout.channel.recv_ready():
        print(stdout.channel.recv(4096).decode('gbk', errors='ignore'))
    if stderr.channel.recv_ready():
        print(stderr.channel.recv(4096).decode('gbk', errors='ignore'))
    
    print("\n=== 检查端口8080 ===")
    stdin2, stdout2, stderr2 = client.exec_command('netstat -an | findstr 8080')
    print(stdout2.read().decode('gbk', errors='ignore'))
    
    client.close()
    print("\n完成")

if __name__ == '__main__':
    main()
