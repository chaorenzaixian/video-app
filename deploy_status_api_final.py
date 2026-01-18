#!/usr/bin/env python3
"""
部署转码状态API到转码服务器
包含：部署文件、安装依赖、启动服务、创建计划任务
"""
import paramiko
import time

# 转码服务器配置
TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
BASE_DIR = r'D:\VideoTranscode'

# 状态API代码
STATUS_API_CODE = r'''#!/usr/bin/env python3
"""
转码服务器状态API
部署在转码服务器上，提供状态查询接口
"""
from flask import Flask, jsonify, request
import os
import subprocess
import glob
import shutil

app = Flask(__name__)

BASE_DIR = r"D:\VideoTranscode"
SECRET_KEY = "vYTWoms4FKOqySca1jCLtNHRVz3BAI6U"


def verify_key():
    """验证API密钥"""
    key = request.headers.get('X-Transcode-Key')
    return key == SECRET_KEY


@app.route('/status', methods=['GET'])
def get_status():
    """获取转码系统状态"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # 检查watcher服务状态
    task_running = False
    try:
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'VideoWatcherService', '/fo', 'list'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        task_running = '正在运行' in result.stdout or 'Running' in result.stdout
    except Exception as e:
        print(f"Check task error: {e}")
    
    # 检查PowerShell进程
    ps_count = 0
    try:
        result = subprocess.run(
            ['tasklist', '/fi', 'imagename eq powershell.exe', '/fo', 'csv'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        ps_count = result.stdout.lower().count('powershell.exe')
    except Exception as e:
        print(f"Check PS error: {e}")
    
    # 获取队列文件
    def get_files(path, pattern='*.mp4'):
        try:
            files = glob.glob(os.path.join(path, pattern))
            return [os.path.basename(f) for f in files]
        except:
            return []
    
    def count_dirs(path):
        try:
            if not os.path.exists(path):
                return 0
            return len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
        except:
            return 0
    
    # 获取磁盘空间
    disk_info = []
    for drive in ['C:', 'D:']:
        try:
            total, used, free = shutil.disk_usage(drive)
            disk_info.append({
                'drive': drive,
                'free_gb': round(free / (1024**3), 1),
                'total_gb': round(total / (1024**3), 1),
                'used_percent': round(used / total * 100, 1)
            })
        except Exception as e:
            print(f"Disk {drive} error: {e}")
    
    return jsonify({
        'service': {
            'watcher_running': task_running,
            'powershell_processes': ps_count,
            'status': 'running' if task_running or ps_count > 0 else 'stopped'
        },
        'queue': {
            'short_pending': get_files(os.path.join(BASE_DIR, 'downloads', 'short')),
            'long_pending': get_files(os.path.join(BASE_DIR, 'downloads', 'long')),
            'processing': get_files(os.path.join(BASE_DIR, 'processing')),
            'short_pending_count': len(get_files(os.path.join(BASE_DIR, 'downloads', 'short'))),
            'long_pending_count': len(get_files(os.path.join(BASE_DIR, 'downloads', 'long'))),
            'processing_count': len(get_files(os.path.join(BASE_DIR, 'processing')))
        },
        'completed': {
            'short_count': count_dirs(os.path.join(BASE_DIR, 'completed', 'short')),
            'long_count': count_dirs(os.path.join(BASE_DIR, 'completed', 'long'))
        },
        'disk': disk_info
    })


@app.route('/logs', methods=['GET'])
def get_logs():
    """获取转码日志"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    lines = request.args.get('lines', 50, type=int)
    log_file = os.path.join(BASE_DIR, 'logs', 'watcher.log')
    
    log_entries = []
    try:
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'total': 0, 'message': 'Log file not found'})
            
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    timestamp = parts[0].strip()
                    message = parts[1].strip()
                    
                    level = 'info'
                    if 'Error' in message or 'Failed' in message or 'error' in message.lower():
                        level = 'error'
                    elif 'OK' in message or 'Done' in message or 'Success' in message or 'success' in message.lower():
                        level = 'success'
                    
                    log_entries.append({
                        'timestamp': timestamp,
                        'message': message,
                        'level': level
                    })
                else:
                    log_entries.append({
                        'timestamp': '',
                        'message': line,
                        'level': 'info'
                    })
    except Exception as e:
        return jsonify({'error': str(e), 'logs': [], 'total': 0}), 500
    
    return jsonify({
        'logs': log_entries,
        'total': len(log_entries)
    })


@app.route('/service/restart', methods=['POST'])
def restart_service():
    """重启Watcher服务"""
    if not verify_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # 停止现有PowerShell进程
        subprocess.run(['taskkill', '/f', '/im', 'powershell.exe'], 
                      capture_output=True, errors='ignore')
        
        time.sleep(2)
        
        # 重新启动计划任务
        subprocess.run(['schtasks', '/run', '/tn', 'VideoWatcherService'],
                      capture_output=True, errors='ignore')
        
        time.sleep(3)
        
        # 检查状态
        result = subprocess.run(
            ['schtasks', '/query', '/tn', 'VideoWatcherService', '/fo', 'list'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        running = '正在运行' in result.stdout or 'Running' in result.stdout
        
        return jsonify({
            'success': True,
            'running': running,
            'message': '服务已重启' if running else '服务重启中...'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查（无需认证）"""
    return jsonify({'status': 'ok', 'service': 'transcode-status-api'})


if __name__ == '__main__':
    import time
    print(f"Starting Transcode Status API on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
'''

# 启动脚本
START_SCRIPT = r'''@echo off
cd /d D:\VideoTranscode
echo Starting Status API...
python status_api.py
pause
'''

# 后台启动脚本（使用pythonw或隐藏窗口）
START_HIDDEN_SCRIPT = r'''
$scriptPath = "D:\VideoTranscode\status_api.py"
Start-Process -FilePath "python" -ArgumentList $scriptPath -WindowStyle Hidden -WorkingDirectory "D:\VideoTranscode"
Write-Host "Status API started in background"
'''


def main():
    print("=" * 60)
    print("部署转码状态API")
    print("=" * 60)
    
    # 连接转码服务器
    print(f"\n连接转码服务器 {TRANSCODE_HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
        print("✓ 连接成功")
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return
    
    sftp = ssh.open_sftp()
    
    # 1. 检查并安装Flask
    print("\n1. 检查Flask依赖...")
    stdin, stdout, stderr = ssh.exec_command('python -c "import flask; print(flask.__version__)"')
    flask_version = stdout.read().decode().strip()
    flask_error = stderr.read().decode().strip()
    
    if flask_error or not flask_version:
        print("   Flask未安装，正在安装...")
        stdin, stdout, stderr = ssh.exec_command('pip install flask -i https://pypi.tuna.tsinghua.edu.cn/simple')
        time.sleep(10)
        output = stdout.read().decode()
        print(f"   安装输出: {output[:200]}...")
    else:
        print(f"   ✓ Flask已安装: {flask_version}")
    
    # 2. 部署status_api.py
    print("\n2. 部署status_api.py...")
    api_path = f'{BASE_DIR}\\status_api.py'
    try:
        with sftp.file(api_path, 'w') as f:
            f.write(STATUS_API_CODE)
        print(f"   ✓ 已写入 {api_path}")
    except Exception as e:
        print(f"   ✗ 写入失败: {e}")
        return
    
    # 3. 部署启动脚本
    print("\n3. 部署启动脚本...")
    start_bat_path = f'{BASE_DIR}\\start_status_api.bat'
    try:
        with sftp.file(start_bat_path, 'w') as f:
            f.write(START_SCRIPT)
        print(f"   ✓ 已写入 {start_bat_path}")
    except Exception as e:
        print(f"   ✗ 写入失败: {e}")
    
    # 4. 停止可能存在的旧进程
    print("\n4. 停止旧的API进程...")
    # 查找并杀死占用5001端口的进程
    stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
    port_info = stdout.read().decode('gbk', errors='ignore')
    if port_info:
        print(f"   端口5001占用情况:\n{port_info}")
        # 提取PID并杀死
        for line in port_info.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                if pid.isdigit():
                    print(f"   杀死进程 PID={pid}")
                    ssh.exec_command(f'taskkill /f /pid {pid}')
        time.sleep(2)
    else:
        print("   端口5001未被占用")
    
    # 5. 启动API服务
    print("\n5. 启动Status API服务...")
    # 使用PowerShell在后台启动
    start_cmd = f'powershell -Command "Start-Process -FilePath python -ArgumentList \'{BASE_DIR}\\status_api.py\' -WindowStyle Hidden -WorkingDirectory \'{BASE_DIR}\'"'
    stdin, stdout, stderr = ssh.exec_command(start_cmd)
    time.sleep(3)
    
    # 6. 验证服务是否启动
    print("\n6. 验证服务状态...")
    time.sleep(2)
    
    # 检查端口
    stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
    port_info = stdout.read().decode('gbk', errors='ignore')
    if ':5001' in port_info:
        print(f"   ✓ 端口5001已监听")
        print(f"   {port_info.strip()}")
    else:
        print("   ✗ 端口5001未监听，尝试直接启动查看错误...")
        # 直接运行看错误
        stdin, stdout, stderr = ssh.exec_command(f'cd /d {BASE_DIR} && python status_api.py', timeout=5)
        time.sleep(3)
        err = stderr.read().decode('gbk', errors='ignore')
        out = stdout.read().decode('gbk', errors='ignore')
        if err:
            print(f"   错误: {err}")
        if out:
            print(f"   输出: {out}")
    
    # 7. 测试API
    print("\n7. 测试API健康检查...")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
    health_response = stdout.read().decode()
    if 'ok' in health_response:
        print(f"   ✓ API响应正常: {health_response}")
    else:
        print(f"   ✗ API响应异常: {health_response}")
        # 检查Python进程
        stdin, stdout, stderr = ssh.exec_command('tasklist /fi "imagename eq python.exe"')
        print(f"   Python进程:\n{stdout.read().decode('gbk', errors='ignore')}")
    
    # 8. 创建计划任务（开机自启）
    print("\n8. 创建开机自启计划任务...")
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>python</Command>
      <Arguments>{BASE_DIR}\\status_api.py</Arguments>
      <WorkingDirectory>{BASE_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
    
    # 删除旧任务
    ssh.exec_command('schtasks /delete /tn "TranscodeStatusAPI" /f')
    time.sleep(1)
    
    # 使用简单命令创建任务
    create_task_cmd = f'schtasks /create /tn "TranscodeStatusAPI" /tr "python {BASE_DIR}\\status_api.py" /sc onstart /ru SYSTEM /rl HIGHEST /f'
    stdin, stdout, stderr = ssh.exec_command(create_task_cmd)
    task_result = stdout.read().decode('gbk', errors='ignore')
    task_error = stderr.read().decode('gbk', errors='ignore')
    
    if '成功' in task_result or 'SUCCESS' in task_result.upper():
        print(f"   ✓ 计划任务创建成功")
    else:
        print(f"   计划任务结果: {task_result}")
        if task_error:
            print(f"   错误: {task_error}")
    
    # 9. 最终状态检查
    print("\n" + "=" * 60)
    print("部署完成，最终状态检查")
    print("=" * 60)
    
    # 再次检查端口
    stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
    port_info = stdout.read().decode('gbk', errors='ignore')
    
    if ':5001' in port_info:
        print("\n✓ Status API 已成功启动!")
        print(f"  - 本地访问: http://localhost:5001/health")
        print(f"  - 远程访问: http://{TRANSCODE_HOST}:5001/health")
        print(f"  - 状态接口: http://{TRANSCODE_HOST}:5001/status")
        print(f"  - 日志接口: http://{TRANSCODE_HOST}:5001/logs")
    else:
        print("\n✗ Status API 启动失败，请手动检查")
        print(f"  1. 远程桌面连接到 {TRANSCODE_HOST}")
        print(f"  2. 运行 {BASE_DIR}\\start_status_api.bat")
        print(f"  3. 查看错误信息")
    
    sftp.close()
    ssh.close()
    print("\n部署脚本执行完毕")


if __name__ == '__main__':
    main()
