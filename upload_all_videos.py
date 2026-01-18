#!/usr/bin/env python3
"""
上传所有已完成的视频到主服务器
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("📤 上传所有已完成的视频到主服务器")
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
    
    # 获取所有已完成的视频
    print("📋 获取已完成的视频列表...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*.mp4 /b', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    
    if not files:
        print("  ❌ 没有已完成的视频")
        sys.exit(0)
    
    file_list = [f.strip() for f in files.split('\n') if f.strip()]
    print(f"  找到 {len(file_list)} 个视频文件")
    
    # 过滤掉空文件
    valid_files = []
    for f in file_list:
        stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\short\\{f}\').Length"', timeout=30)
        size = stdout.read().decode('utf-8', errors='ignore').strip()
        try:
            size_bytes = int(size)
            if size_bytes > 1000:  # 大于 1KB
                valid_files.append((f, size_bytes))
        except:
            pass
    
    print(f"  有效文件: {len(valid_files)} 个")
    
    # 上传每个文件
    print("\n📤 开始上传...")
    print("-" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, (filename, size_bytes) in enumerate(valid_files):
        size_mb = size_bytes / (1024 * 1024)
        print(f"\n[{i+1}/{len(valid_files)}] {filename} ({size_mb:.1f} MB)")
        
        # 构建 SCP 命令
        local_file = f'D:\\VideoTranscode\\completed\\short\\{filename}'
        remote_path = '/www/wwwroot/video-app/backend/uploads/shorts/'
        
        scp_cmd = f'scp -i C:\\server_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL "{local_file}" root@38.47.218.137:{remote_path}'
        
        print(f"  上传中...")
        start_time = time.time()
        
        stdin, stdout, stderr = ssh.exec_command(scp_cmd, timeout=600)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()
        
        elapsed = time.time() - start_time
        
        # 验证上传
        stdin, stdout, stderr = ssh.exec_command(f'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la \'{remote_path}{filename}\' 2>/dev/null"', timeout=30)
        verify = stdout.read().decode('utf-8', errors='ignore').strip()
        
        if filename in verify:
            print(f"  ✅ 成功 ({elapsed:.1f}秒)")
            success_count += 1
        else:
            print(f"  ❌ 失败")
            if error:
                print(f"  错误: {error[:100]}")
            fail_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 上传完成")
    print("=" * 60)
    print(f"\n✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"📊 总计: {len(valid_files)}")
    
    # 检查主服务器上的文件
    print("\n📋 主服务器上的文件:")
    stdin, stdout, stderr = ssh.exec_command('ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -la /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | tail -10"', timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore').strip()
    if output:
        for line in output.split('\n')[-10:]:
            if line.strip():
                print(f"  {line}")
    
except Exception as e:
    print(f"\n❌ 上传失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
