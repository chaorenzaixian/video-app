"""
完成转码服务设置
"""
import paramiko

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建VBS启动脚本
    vbs_content = 'Set WshShell = CreateObject("WScript.Shell")\n'
    vbs_content += 'WshShell.CurrentDirectory = "D:\\VideoTranscode\\service"\n'
    vbs_content += 'WshShell.Run "python service.py", 0, False\n'
    
    with sftp.file('D:/VideoTranscode/start_hidden.vbs', 'w') as f:
        f.write(vbs_content)
    print('已更新 start_hidden.vbs')
    
    sftp.close()
    
    # 更新计划任务
    print('\n更新计划任务...')
    cmd = 'schtasks /create /tn "VideoTranscodeService" /tr "wscript.exe D:\\VideoTranscode\\start_hidden.vbs" /sc onstart /ru Administrator /rp "jCkMIjNlnSd7f6GM" /f'
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('gbk', errors='ignore'))
    
    # 检查当前服务状态
    print('\n当前服务状态:')
    stdin, stdout, stderr = client.exec_command('netstat -an | findstr 8080')
    result = stdout.read().decode('gbk', errors='ignore')
    print(result)
    
    if 'LISTENING' in result:
        print('\n✓ 服务正在运行！')
        
        # 测试Web界面
        print('\n测试Web界面...')
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/ | head -c 200')
        html = stdout.read().decode('utf-8', errors='ignore')
        if '视频转码' in html or '<html' in html.lower():
            print('✓ Web界面正常')
        
        # 测试API
        print('\n测试API...')
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:8080/api/categories')
        api_result = stdout.read().decode('utf-8', errors='ignore')
        if 'categories' in api_result:
            print('✓ API正常')
        
        print('\n' + '=' * 50)
        print('  转码服务设置完成！')
        print('=' * 50)
        print('\nWeb管理界面: http://198.176.60.121:8080')
        print('\n功能:')
        print('  - 上传视频自动转码')
        print('  - 选择封面')
        print('  - 设置标题/分类/标签')
        print('  - 设置VIP/金币价格')
        print('  - 一键发布到主服务器')
        print('\n服务会在系统重启后自动启动')
    else:
        print('\n✗ 服务未运行')
    
    client.close()

if __name__ == '__main__':
    main()
