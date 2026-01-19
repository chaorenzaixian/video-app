# 检查转码服务器上已完成视频的封面
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
    
    # 检查已完成目录中的封面
    print("=== 检查已完成视频的封面 ===")
    stdin, stdout, stderr = ssh.exec_command('dir /s D:\\VideoTranscode\\completed\\long\\*\\covers\\')
    output = stdout.read().decode('gbk', errors='ignore')
    print(output if output.strip() else "没有找到封面目录")
    
    # 检查一个具体的视频目录
    print("\n=== 检查具体视频目录结构 ===")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\long\\萝莉\\')
    print(stdout.read().decode('gbk', errors='ignore'))
    
    ssh.close()

if __name__ == "__main__":
    main()
