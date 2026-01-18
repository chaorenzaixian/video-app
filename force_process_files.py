#!/usr/bin/env python3
"""
强制处理文件 - 手动调用转码
"""
import paramiko
import sys
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

print("🔧 强制处理文件")
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
    
    # 1. 获取所有待处理文件
    print("📁 获取待处理文件...")
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\short\\*.mp4 /b', timeout=30)
    files = stdout.read().decode('gbk', errors='ignore').strip()
    file_list = [f.strip() for f in files.split('\n') if f.strip()]
    
    print(f"  找到 {len(file_list)} 个文件:")
    for f in file_list:
        print(f"    - {f}")
    
    if not file_list:
        print("\n  ❌ 没有待处理文件")
        sys.exit(0)
    
    # 2. 逐个处理文件
    print("\n📋 开始处理文件...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, filename in enumerate(file_list):
        print(f"\n[{i+1}/{len(file_list)}] 处理: {filename}")
        print("-" * 60)
        
        # 移动到 processing
        source = f'D:\\VideoTranscode\\downloads\\short\\{filename}'
        dest = f'D:\\VideoTranscode\\processing\\{filename}'
        
        print(f"  1. 移动文件到 processing...")
        stdin, stdout, stderr = ssh.exec_command(f'move "{source}" "{dest}"', timeout=30)
        output = stdout.read().decode('gbk', errors='ignore').strip()
        
        if '1 个文件' in output or '1 file' in output:
            print(f"    ✅ 已移动")
        else:
            print(f"    ❌ 移动失败: {output}")
            fail_count += 1
            continue
        
        # 调用转码脚本
        print(f"  2. 开始转码...")
        cmd = f'powershell -ExecutionPolicy Bypass -File D:\\VideoTranscode\\scripts\\transcode_full.ps1 -InputFile "{dest}" -VideoType "short"'
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
        
        # 读取输出
        output_lines = []
        error_lines = []
        
        try:
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            output_lines = output.split('\n')
        except:
            pass
        
        try:
            error = stderr.read().decode('utf-8', errors='ignore').strip()
            error_lines = error.split('\n')
        except:
            pass
        
        # 显示最后几行输出
        if output_lines:
            print(f"    输出:")
            for line in output_lines[-5:]:
                if line.strip():
                    print(f"      {line}")
        
        if error_lines and any('error' in l.lower() or 'failed' in l.lower() for l in error_lines):
            print(f"    错误:")
            for line in error_lines[-3:]:
                if line.strip():
                    print(f"      {line}")
        
        # 检查是否成功
        output_file = f'D:\\VideoTranscode\\completed\\short\\{filename.replace(".mp4", "_transcoded.mp4")}'
        stdin, stdout, stderr = ssh.exec_command(f'dir "{output_file}" 2>nul', timeout=30)
        result = stdout.read().decode('gbk', errors='ignore').strip()
        
        if filename.replace(".mp4", "_transcoded.mp4") in result:
            print(f"    ✅ 转码成功!")
            success_count += 1
        else:
            print(f"    ❌ 转码失败")
            fail_count += 1
        
        # 短暂延迟
        if i < len(file_list) - 1:
            time.sleep(2)
    
    # 3. 总结
    print("\n" + "=" * 60)
    print("📊 处理完成")
    print("=" * 60)
    print(f"\n✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"📊 总计: {len(file_list)}")
    
    # 4. 检查最终状态
    print("\n📁 最终文件状态:")
    
    stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\short\\*_transcoded.mp4 /b 2>nul', timeout=30)
    completed = stdout.read().decode('gbk', errors='ignore').strip()
    completed_files = [f.strip() for f in completed.split('\n') if f.strip() and 'test_' not in f]
    
    if completed_files:
        print(f"\n  ✅ 已完成 {len(completed_files)} 个文件:")
        for f in completed_files:
            # 获取文件大小
            stdin, stdout, stderr = ssh.exec_command(f'powershell -Command "(Get-Item \'D:\\VideoTranscode\\completed\\short\\{f}\').Length / 1MB"', timeout=30)
            size = stdout.read().decode('utf-8', errors='ignore').strip()
            try:
                size_mb = float(size)
                print(f"    - {f} ({size_mb:.1f} MB)")
            except:
                print(f"    - {f}")
    
    if success_count == len(file_list):
        print("\n🎉 所有文件处理成功!")
    elif success_count > 0:
        print(f"\n⚠️ 部分文件处理成功 ({success_count}/{len(file_list)})")
    else:
        print("\n❌ 所有文件处理失败")
        print("\n💡 建议:")
        print("1. 检查转码脚本语法")
        print("2. 检查 FFmpeg 是否可用")
        print("3. 查看转码日志: D:\\VideoTranscode\\logs\\transcode.log")
    
except Exception as e:
    print(f"\n❌ 处理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'ssh' in locals():
        ssh.close()
