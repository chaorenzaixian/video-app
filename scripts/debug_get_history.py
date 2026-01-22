"""调试get_history函数"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 创建测试脚本
script = '''
import sys
sys.path.insert(0, r'D:\\VideoTranscode\\service')

import web_ui
from flask import jsonify

# 打印get_history函数的源代码
import inspect
print("=== get_history函数源代码 ===")
print(inspect.getsource(web_ui.get_history))

# 手动调用get_history
print("\\n=== 手动调用get_history ===")
with web_ui.app.app_context():
    # 模拟请求
    with web_ui.app.test_request_context('/api/history'):
        result = web_ui.get_history()
        print(f"返回类型: {type(result)}")
        print(f"返回值: {result.get_json()}")
'''

sftp = ssh.open_sftp()
with sftp.file('D:/debug_gh.py', 'w') as f:
    f.write(script)
sftp.close()

print('执行测试...')
stdin, stdout, stderr = ssh.exec_command('python D:\\debug_gh.py', timeout=60)
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print(output)
if error:
    print('Stderr:', error)

ssh.close()
