"""测试封面生成速度和智能选择"""
import paramiko
import os

HOST = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

# 测试脚本内容
test_script = '''
import os, sys, time
sys.path.insert(0, r"D:\\VideoTranscode\\service")
os.chdir(r"D:\\VideoTranscode\\service")

from transcoder import Transcoder

# 找视频
test_video = None
for root, dirs, files in os.walk(r"D:\\VideoTranscode\\completed"):
    for f in files:
        if f.lower().endswith('.mp4'):
            test_video = os.path.join(root, f)
            break
    if test_video:
        break

if not test_video:
    print("没有找到视频!")
    sys.exit(1)

print(f"视频: {test_video}")
print(f"大小: {os.path.getsize(test_video)/1024/1024:.1f}MB")

t = Transcoder()
dur, h = t.get_video_info(test_video)
print(f"时长: {dur:.1f}s, 高度: {h}p")

import tempfile, shutil
tmp = tempfile.mkdtemp()
print(f"\\n生成封面中...")
start = time.time()
covers_dir, best = t.generate_covers(test_video, tmp, dur)
elapsed = time.time() - start
print(f"\\n=== 结果 ===")
print(f"耗时: {elapsed:.2f}秒")
print(f"最佳封面: cover_{best}.webp")

for f in sorted(os.listdir(covers_dir)):
    sz = os.path.getsize(os.path.join(covers_dir, f))/1024
    print(f"  {f}: {sz:.1f}KB")

shutil.rmtree(tmp)
print("\\n测试完成!")
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

# 上传测试脚本
sftp = ssh.open_sftp()
remote_path = "D:/VideoTranscode/test_cover.py"
with sftp.file(remote_path, 'w') as f:
    f.write(test_script)
sftp.close()

print("运行封面生成测试...")
print("=" * 50)

# 运行测试
stdin, stdout, stderr = ssh.exec_command(f'python "{remote_path}"', timeout=300)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')

print(out)
if err:
    print(f"\n错误:\n{err}")

# 清理
ssh.exec_command(f'del "{remote_path}"')
ssh.close()
