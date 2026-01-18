#!/usr/bin/env python3
"""上传新测试视频到转码服务器"""
import paramiko
import time

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    # 列出 completed/short 目录的文件
    print('📁 查看 completed/short 目录...')
    stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\completed\\short\\*.mp4"', timeout=30)
    out = stdout.read().decode('gbk', errors='ignore')
    print(out)
    
    # 使用 PowerShell 复制文件（更好的中文支持）
    print('\n📋 复制测试视频...')
    test_name = f"new_test_{int(time.time())}"
    
    # 先找一个英文名的文件
    cmd = '''powershell -Command "Get-ChildItem 'D:\\VideoTranscode\\completed\\short\\*.mp4' | Where-Object { $_.Name -match '^[a-zA-Z0-9_]+' } | Select-Object -First 1 -ExpandProperty Name"'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    eng_file = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if eng_file:
        print(f'  找到英文名文件: {eng_file}')
        # 复制到 downloads
        cmd = f'copy "D:\\VideoTranscode\\completed\\short\\{eng_file}" "D:\\VideoTranscode\\downloads\\short\\{test_name}.mp4"'
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        out = stdout.read().decode('gbk', errors='ignore')
        print(f'  复制结果: {out}')
    else:
        print('  没有找到英文名文件，尝试用 PowerShell 复制第一个文件...')
        cmd = f'''powershell -Command "$files = Get-ChildItem 'D:\\VideoTranscode\\completed\\short\\*.mp4'; if ($files.Count -gt 0) {{ Copy-Item $files[0].FullName 'D:\\VideoTranscode\\downloads\\short\\{test_name}.mp4' -Force; Write-Host 'Copied:' $files[0].Name }}"'''
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        print(f'  结果: {out}')
        if err:
            print(f'  错误: {err}')
    
    # 验证文件是否存在
    print('\n🔍 验证文件...')
    stdin, stdout, stderr = ssh.exec_command(f'dir "D:\\VideoTranscode\\downloads\\short\\{test_name}.mp4"', timeout=30)
    out = stdout.read().decode('gbk', errors='ignore')
    if test_name in out:
        print(f'  ✓ 文件已创建: {test_name}.mp4')
        print('\n⏳ Watcher 将在下一个检查周期处理此文件')
        print('  处理完成后会出现在"待处理视频"列表中')
    else:
        print('  ✗ 文件创建失败')
        print(out)
    
    # 手动触发 watcher
    print('\n🔄 手动触发 Watcher...')
    stdin, stdout, stderr = ssh.exec_command('schtasks /run /tn "VideoWatcherService"', timeout=30)
    out = stdout.read().decode('gbk', errors='ignore')
    print(f'  {out}')
    
    ssh.close()
    print('\n✅ 完成！请等待 1-2 分钟后刷新"待处理视频"页面')

if __name__ == '__main__':
    main()
