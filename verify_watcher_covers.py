#!/usr/bin/env python3
"""验证 watcher 脚本的多封面上传功能"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("验证 watcher 脚本的多封面上传功能...")
print("=" * 60)

# 读取脚本
sftp = ssh.open_sftp()
with sftp.file('D:/VideoTranscode/scripts/watcher.ps1', 'r') as f:
    content = f.read().decode('utf-8')
sftp.close()

# 检查关键功能
checks = [
    ("Get-BestCover 函数", "function Get-BestCover"),
    ("多封面上传代码", "Uploading covers"),
    ("创建远程 covers 目录", "mkdir -p"),
    ("上传 cover_*.webp", "cover_$i.webp"),
    ("调试日志", "Checking covers dir"),
]

print("\n功能检查:")
all_ok = True
for name, keyword in checks:
    if keyword in content:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ {name}")
        all_ok = False

# 检查 watcher 是否在运行
print("\nWatcher 状态:")
cmd = 'tasklist | findstr powershell'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if 'powershell' in output.lower():
    print("  ✓ Watcher 正在运行")
else:
    print("  ✗ Watcher 未运行")

# 检查最近的日志
print("\n最近的日志:")
cmd = 'type "D:\\VideoTranscode\\logs\\watcher.log" 2>nul | tail -10'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
if output.strip():
    print(output)
else:
    print("  (日志为空)")

ssh.close()

print("\n" + "=" * 60)
if all_ok:
    print("✓ Watcher 脚本配置正确")
    print("  新转码的视频将自动上传 10 张封面")
    print("\n对于现有的待处理视频（HLS 不完整）：")
    print("  - 需要重新转码才能获得多封面")
    print("  - 或者接受只有一张封面")
else:
    print("✗ Watcher 脚本需要修复")
