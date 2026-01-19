# 检查转码服务器状态和日志
import paramiko

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print(f"连接转码服务器 {HOST}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    
    print("连接成功！\n")
    
    # 1. 检查 watcher.log 最后100行
    print("=== watcher.log 最后100行 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 100"')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 2. 检查已完成目录
    print("\n=== 已完成目录 (最新) ===")
    stdin, stdout, stderr = ssh.exec_command('dir /od D:\\VideoTranscode\\completed\\long\\')
    print(stdout.read().decode('gbk', errors='ignore'))
    
    ssh.close()

if __name__ == "__main__":
    main()
