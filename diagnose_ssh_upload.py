#!/usr/bin/env python3
"""
诊断 SSH 上传问题
"""
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 诊断 SSH 上传问题")
print("=" * 60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh.connect(
        hostname=TRANSCODE_SERVER,
        port=22,
        username=TRANSCODE_USER,
        password=TRANSCODE_PASSWORD,
        timeout=30
    )
    
    # 1. 检查 SSH 密钥文件
    print("📋 1. 检查 SSH 密钥文件:")
    stdin, stdout, stderr = ssh.exec_command('type C:\\server_key', timeout=30)
    key_content = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if key_content:
        # 只显示前几行
        lines = key_content.split('\n')
        print(f"  密钥文件存在，共 {len(lines)} 行")
        print(f"  第一行: {lines[0][:50]}...")
        print(f"  最后一行: {lines[-1][:50]}...")
    else:
        print("  ❌ 密钥文件为空或不存在")
    
    # 2. 检查密钥权限
    print("\n📋 2. 检查密钥文件属性:")
    stdin, stdout, stderr = ssh.exec_command('dir C:\\server_key', timeout=30)
    output = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  {output}")
    
    # 3. 测试 SSH 连接
    print("\n📋 3. 测试 SSH 连接到主服务器:")
    stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10 root@38.47.218.137 "echo SSH_OK"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    if 'SSH_OK' in output:
        print("  ✅ SSH 连接成功!")
    else:
        print(f"  ❌ SSH 连接失败")
        print(f"  输出: {output}")
        print(f"  错误: {error}")
    
    # 4. 检查 SCP 命令
    print("\n📋 4. 检查 SCP 命令:")
    stdin, stdout, stderr = ssh.exec_command('scp -V 2>&1', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    print(f"  {output or error}")
    
    # 5. 测试简单的 SCP 上传
    print("\n📋 5. 测试 SCP 上传（创建测试文件）:")
    
    # 创建一个小测试文件
    stdin, stdout, stderr = ssh.exec_command('echo test > D:\\VideoTranscode\\test_upload.txt', timeout=30)
    stdout.read()
    
    # 尝试上传
    stdin, stdout, stderr = ssh.exec_command('scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL D:\\VideoTranscode\\test_upload.txt root@38.47.218.137:/tmp/', timeout=60)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    print(f"  输出: {output}")
    print(f"  错误: {error}")
    
    # 检查退出码
    stdin, stdout, stderr = ssh.exec_command('echo %ERRORLEVEL%', timeout=30)
    exit_code = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  退出码: {exit_code}")
    
    # 6. 检查主服务器目录
    print("\n📋 6. 检查主服务器目录:")
    stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/shorts/ 2>&1 | head -5"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    if output:
        print(f"  {output}")
    else:
        print(f"  错误: {error}")
    
    # 清理测试文件
    stdin, stdout, stderr = ssh.exec_command('del D:\\VideoTranscode\\test_upload.txt 2>nul', timeout=30)
    stdout.read()
    
except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
