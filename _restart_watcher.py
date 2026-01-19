# 检查脚本编码问题
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
    
    # 检查脚本第467行附近
    print("=== 检查脚本第460-470行 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-Object -Skip 459 -First 15"')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    # 检查脚本第110-115行
    print("\n=== 检查脚本第110-120行 ===")
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\scripts\\watcher.ps1 | Select-Object -Skip 109 -First 15"')
    print(stdout.read().decode('utf-8', errors='ignore'))
    
    ssh.close()

if __name__ == "__main__":
    main()
