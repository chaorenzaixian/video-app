#!/usr/bin/env python3
"""收集转码系统完整状态报告"""
import paramiko
import json
from datetime import datetime

def main():
    print("=" * 70)
    print("转码系统完整状态报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 连接转码服务器
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM', timeout=30)
    
    # ============ 1. Watcher服务状态 ============
    print("\n" + "=" * 50)
    print("1. WATCHER 服务状态")
    print("=" * 50)
    
    # 计划任务状态
    stdin, stdout, stderr = ssh.exec_command('schtasks /query /tn "VideoWatcherService" /v /fo list 2>nul')
    task_info = stdout.read().decode('gbk', errors='ignore')
    
    if '正在运行' in task_info:
        print("✓ 计划任务状态: 正在运行")
    elif '就绪' in task_info:
        print("⚠ 计划任务状态: 就绪（未运行）")
    else:
        print("✗ 计划任务状态: 未知")
    
    # PowerShell进程
    stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq powershell.exe" /fo csv')
    ps_info = stdout.read().decode('gbk', errors='ignore')
    ps_count = ps_info.count('powershell.exe')
    print(f"  PowerShell进程数: {ps_count}")
    
    # ============ 2. 目录状态 ============
    print("\n" + "=" * 50)
    print("2. 目录状态")
    print("=" * 50)
    
    dirs = {
        'downloads/short': 'D:\\VideoTranscode\\downloads\\short',
        'downloads/long': 'D:\\VideoTranscode\\downloads\\long',
        'processing': 'D:\\VideoTranscode\\processing',
        'completed/short': 'D:\\VideoTranscode\\completed\\short',
        'completed/long': 'D:\\VideoTranscode\\completed\\long',
    }
    
    for name, path in dirs.items():
        stdin, stdout, stderr = ssh.exec_command(f'dir /b "{path}" 2>nul | find /c /v ""')
        count = stdout.read().decode('gbk', errors='ignore').strip()
        try:
            count = int(count)
        except:
            count = 0
        status = "✓" if count == 0 or name.startswith('completed') else "⚠"
        print(f"  {status} {name}: {count} 个文件")
    
    # ============ 3. 待处理视频 ============
    print("\n" + "=" * 50)
    print("3. 待处理视频队列")
    print("=" * 50)
    
    # 短视频队列
    stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\downloads\\short\\*.mp4" 2>nul')
    short_queue = [f for f in stdout.read().decode('gbk', errors='ignore').strip().split('\n') if f.strip()]
    print(f"  短视频队列: {len(short_queue)} 个")
    for f in short_queue[:5]:
        print(f"    - {f}")
    if len(short_queue) > 5:
        print(f"    ... 还有 {len(short_queue) - 5} 个")
    
    # 长视频队列
    stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\downloads\\long\\*.mp4" 2>nul')
    long_queue = [f for f in stdout.read().decode('gbk', errors='ignore').strip().split('\n') if f.strip()]
    print(f"  长视频队列: {len(long_queue)} 个")
    for f in long_queue[:5]:
        print(f"    - {f}")
    if len(long_queue) > 5:
        print(f"    ... 还有 {len(long_queue) - 5} 个")
    
    # 正在处理
    stdin, stdout, stderr = ssh.exec_command('dir /b "D:\\VideoTranscode\\processing\\*.mp4" 2>nul')
    processing = [f for f in stdout.read().decode('gbk', errors='ignore').strip().split('\n') if f.strip()]
    print(f"  正在处理: {len(processing)} 个")
    for f in processing:
        print(f"    - {f}")
    
    # ============ 4. 已完成视频统计 ============
    print("\n" + "=" * 50)
    print("4. 已完成视频统计")
    print("=" * 50)
    
    # 短视频
    stdin, stdout, stderr = ssh.exec_command('dir /b /ad "D:\\VideoTranscode\\completed\\short" 2>nul | find /c /v ""')
    short_completed = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  短视频已完成: {short_completed} 个")
    
    # 长视频
    stdin, stdout, stderr = ssh.exec_command('dir /b /ad "D:\\VideoTranscode\\completed\\long" 2>nul | find /c /v ""')
    long_completed = stdout.read().decode('gbk', errors='ignore').strip()
    print(f"  长视频已完成: {long_completed} 个")
    
    # ============ 5. 最近日志 ============
    print("\n" + "=" * 50)
    print("5. 最近转码日志 (最后20条)")
    print("=" * 50)
    
    stdin, stdout, stderr = ssh.exec_command('powershell -Command "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 20"')
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)
    
    # ============ 6. 磁盘空间 ============
    print("\n" + "=" * 50)
    print("6. 磁盘空间")
    print("=" * 50)
    
    stdin, stdout, stderr = ssh.exec_command('wmic logicaldisk get size,freespace,caption')
    disk_info = stdout.read().decode('gbk', errors='ignore')
    print(disk_info)
    
    # ============ 7. 主服务器数据库状态 ============
    print("\n" + "=" * 50)
    print("7. 主服务器数据库状态")
    print("=" * 50)
    
    # REVIEWING状态视频
    cmd = "ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 \"PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -t -c \\\"SELECT COUNT(*) FROM videos WHERE status = 'REVIEWING'\\\"\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    reviewing_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  待审核视频 (REVIEWING): {reviewing_count} 个")
    
    # PUBLISHED状态视频
    cmd = "ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 \"PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -t -c \\\"SELECT COUNT(*) FROM videos WHERE status = 'PUBLISHED'\\\"\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    published_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  已发布视频 (PUBLISHED): {published_count} 个")
    
    # 最近5条视频
    print("\n  最近5条视频记录:")
    cmd = "ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 \"PGPASSWORD='VideoApp2024!' psql -h 127.0.0.1 -U video_app -d video_app -t -c \\\"SELECT id, title, status, is_short FROM videos ORDER BY id DESC LIMIT 5\\\"\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    recent_videos = stdout.read().decode('utf-8', errors='ignore')
    for line in recent_videos.strip().split('\n'):
        if line.strip():
            print(f"    {line.strip()}")
    
    # ============ 8. 主服务器文件状态 ============
    print("\n" + "=" * 50)
    print("8. 主服务器上传目录状态")
    print("=" * 50)
    
    # shorts目录
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -1 /www/wwwroot/video-app/backend/uploads/shorts/*.mp4 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    shorts_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  shorts目录MP4文件: {shorts_count} 个")
    
    # thumbnails目录
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -1 /www/wwwroot/video-app/backend/uploads/thumbnails/*.webp 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    thumbs_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  thumbnails目录封面: {thumbs_count} 个")
    
    # shorts/thumbnails子目录
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -d /www/wwwroot/video-app/backend/uploads/shorts/thumbnails/*/ 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    cover_dirs = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  shorts/thumbnails封面目录: {cover_dirs} 个")
    
    # hls目录
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "ls -d /www/wwwroot/video-app/backend/uploads/hls/*/ 2>/dev/null | wc -l"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    hls_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  hls目录(长视频): {hls_count} 个")
    
    # ============ 9. 后端服务状态 ============
    print("\n" + "=" * 50)
    print("9. 后端服务状态")
    print("=" * 50)
    
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "systemctl status video-app-backend.service 2>&1 | head -5"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    service_status = stdout.read().decode('utf-8', errors='ignore')
    print(service_status)
    
    # API健康检查
    cmd = 'ssh -i C:\\server_key -o StrictHostKeyChecking=no root@38.47.218.137 "curl -s http://localhost:8000/api/health"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    health = stdout.read().decode('utf-8', errors='ignore')
    print(f"  API健康检查: {health}")
    
    ssh.close()
    
    # ============ 总结 ============
    print("\n" + "=" * 70)
    print("状态总结")
    print("=" * 70)

if __name__ == '__main__':
    main()
