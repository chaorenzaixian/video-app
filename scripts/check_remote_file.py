"""
检查远程web_ui.py内容
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 读取远程文件
    print("读取远程web_ui.py...")
    with sftp.file('D:/VideoTranscode/service/web_ui.py', 'r') as f:
        content = f.read().decode('utf-8')
    
    # 检查是否有recover函数
    if 'recover_pending_tasks' in content:
        print("✓ 找到recover_pending_tasks函数")
        # 找到函数定义的位置
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'def recover_pending_tasks' in line:
                print(f"  位置: 第{i+1}行")
                print(f"  内容: {lines[i:i+3]}")
                break
    else:
        print("✗ 未找到recover_pending_tasks函数")
        print(f"文件大小: {len(content)} 字节")
        print(f"前500字符: {content[:500]}")
    
    sftp.close()
    client.close()

if __name__ == '__main__':
    main()
