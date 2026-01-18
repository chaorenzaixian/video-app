#!/usr/bin/env python3
"""
调试 SCP 命令
"""
import paramiko
import sys

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔍 调试 SCP 命令")
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
    
    # 直接运行 SCP 命令
    print("📋 直接测试 SCP 命令:")
    
    # 创建测试文件
    stdin, stdout, stderr = ssh.exec_command('echo test123 > D:\\VideoTranscode\\test_scp.txt', timeout=30)
    stdout.read()
    
    # 运行 SCP
    scp_cmd = 'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL D:\\VideoTranscode\\test_scp.txt root@38.47.218.137:/tmp/'
    print(f"  命令: {scp_cmd}")
    
    stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=60)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    print(f"  输出: {output}")
    print(f"  错误: {error}")
    
    # 检查退出码
    stdin, stdout, stderr = ssh.exec_command('echo Exit code: %ERRORLEVEL%', timeout=30)
    exit_code = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  {exit_code}")
    
    # 验证文件是否上传成功
    print("\n📋 验证文件是否上传:")
    stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /tmp/test_scp.txt"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    error = stderr.read().decode('utf-8', errors='ignore').strip()
    
    if 'test_scp.txt' in output:
        print(f"  ✅ 文件上传成功!")
        print(f"  {output}")
    else:
        print(f"  ❌ 文件未找到")
        print(f"  错误: {error}")
    
    # 测试上传视频文件
    print("\n📋 测试上传视频文件:")
    
    # 获取一个小的视频文件
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b /o:s', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    
    if files:
        # 选择最小的文件
        smallest_file = files.split('\n')[0].strip()
        print(f"  测试文件: {smallest_file}")
        
        # 获取文件大小
        stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\short\\{smallest_file}\').Length / 1MB"', timeout=30)
        size = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"  文件大小: {size} MB")
        
        # 上传
        scp_cmd = f'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "D:\\VideoTranscode\\completed\\short\\{smallest_file}" root@38.47.218.137:/www/wwwroot/video-app/backend/uploads/shorts/'
        print(f"  命令: {scp_cmd[:100]}...")
        
        stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=300)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        
        print(f"  输出: {output}")
        print(f"  错误: {error}")
        
        # 验证
        stdin, stdout, stderr = ssh.exec_command(f'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/shorts/{smallest_file}"', timeout=30)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        
        if smallest_file in output:
            print(f"  ✅ 视频上传成功!")
            print(f"  {output}")
        else:
            print(f"  ❌ 视频上传失败")
    
    # 清理
    stdin, stdout, stderr = ssh.exec_command('del D:\\VideoTranscode\\test_scp.txt 2>nul', timeout=30)
    stdout.read()
    
except Exception as e:
    print(f"\n❌ 调试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
