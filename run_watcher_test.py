# run_watcher_test.py - 在转码服务器上测试运行watcher脚本
import paramiko
import time

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

def main():
    print("连接到转码服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    print("连接成功!")
    
    # 先确保目录存在
    print("\n确保目录存在...")
    dirs = [
        "D:\\VideoTranscode\\downloads",
        "D:\\VideoTranscode\\processing", 
        "D:\\VideoTranscode\\completed",
        "D:\\VideoTranscode\\logs"
    ]
    for d in dirs:
        ssh.exec_command(f'powershell -Command "New-Item -ItemType Directory -Path \'{d}\' -Force | Out-Null"')
    
    # 运行脚本（只运行几秒钟测试）
    print("\n启动watcher脚本测试（5秒后自动停止）...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -ExecutionPolicy Bypass -Command "& { $job = Start-Job -ScriptBlock { & D:\\VideoTranscode\\scripts\\watcher.ps1 }; Start-Sleep -Seconds 5; Stop-Job $job; Receive-Job $job }"',
        timeout=30
    )
    
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    print("输出:")
    print(output if output else "(无输出)")
    
    if error:
        print("\n错误:")
        print(error)
    
    # 检查日志文件
    print("\n检查日志文件...")
    stdin, stdout, stderr = ssh.exec_command(
        'powershell -Command "Get-ChildItem D:\\VideoTranscode\\logs\\ -ErrorAction SilentlyContinue"'
    )
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output if output else "(无日志文件)")
    
    ssh.close()
    print("\n测试完成!")

if __name__ == "__main__":
    main()
