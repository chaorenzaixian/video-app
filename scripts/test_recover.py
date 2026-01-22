"""
测试恢复函数
"""
import paramiko
import time

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')
    
    sftp = client.open_sftp()
    
    # 创建测试脚本
    test_script = '''
import os
import sys
sys.path.insert(0, r"D:\\VideoTranscode\\service")
from config import DIRS

processing_dir = DIRS["processing"]
print("Processing目录:", processing_dir)
print("存在:", os.path.exists(processing_dir))

for task_dir in os.listdir(processing_dir):
    task_path = os.path.join(processing_dir, task_dir)
    if not os.path.isdir(task_path):
        continue
    hls_dir = os.path.join(task_path, "hls")
    covers_dir = os.path.join(task_path, "covers")
    has_hls = os.path.exists(hls_dir)
    has_covers = os.path.exists(covers_dir)
    print(f"  {task_dir}: hls={has_hls}, covers={has_covers}")
    
    if has_hls and has_covers:
        # 找视频文件
        video_files = [f for f in os.listdir(task_path) 
                      if f.endswith((".mp4", ".mov", ".avi", ".mkv")) and not f.endswith("_preview.webm")]
        print(f"    视频文件: {video_files}")
'''
    
    with sftp.file('D:/VideoTranscode/test_recover.py', 'w') as f:
        f.write(test_script)
    
    sftp.close()
    
    # 运行测试
    print('运行测试...')
    stdin, stdout, stderr = client.exec_command('python D:\\VideoTranscode\\test_recover.py')
    time.sleep(5)
    result = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    print(result)
    if err:
        print('错误:', err)
    
    client.close()

if __name__ == '__main__':
    main()
