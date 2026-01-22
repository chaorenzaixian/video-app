"""
检查web_ui.py内容
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    # 检查web_ui.py是否有recover函数
    print("检查web_ui.py中的recover函数:")
    stdin, stdout, stderr = client.exec_command('findstr "recover_pending" D:\\VideoTranscode\\service\\web_ui.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result if result else "未找到recover_pending函数")
    
    # 检查run_web_ui函数
    print("\n检查run_web_ui函数:")
    stdin, stdout, stderr = client.exec_command('findstr "run_web_ui" D:\\VideoTranscode\\service\\web_ui.py')
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result if result else "未找到")
    
    client.close()

if __name__ == '__main__':
    main()
