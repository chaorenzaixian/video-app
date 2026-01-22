"""
列出processing目录
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    print("Processing目录内容:")
    stdin, stdout, stderr = client.exec_command('dir "D:\\VideoTranscode\\processing" /b')
    result = stdout.read().decode('gbk', errors='ignore')
    dirs = [d.strip() for d in result.split('\n') if d.strip()]
    print(f"共 {len(dirs)} 个项目")
    
    for d in dirs[:5]:
        print(f"\n=== {d} ===")
        stdin, stdout, stderr = client.exec_command(f'dir "D:\\VideoTranscode\\processing\\{d}" /b')
        content = stdout.read().decode('gbk', errors='ignore')
        print(content if content.strip() else "空目录")
        
        # 检查hls
        stdin, stdout, stderr = client.exec_command(f'dir "D:\\VideoTranscode\\processing\\{d}\\hls" /b 2>nul')
        hls = stdout.read().decode('gbk', errors='ignore')
        if hls.strip():
            print(f"HLS: {hls.strip()[:100]}")
    
    client.close()

if __name__ == '__main__':
    main()
