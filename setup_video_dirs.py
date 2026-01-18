# setup_video_dirs.py - 创建视频目录结构
import paramiko

TRANSCODE_SERVER = "198.176.60.121"
TRANSCODE_USER = "Administrator"
TRANSCODE_PASSWORD = "jCkMIjNlnSd7f6GM"

MAIN_SERVER = "38.47.218.137"

def main():
    # 1. 转码服务器目录
    print("1. 创建转码服务器目录...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(TRANSCODE_SERVER, username=TRANSCODE_USER, password=TRANSCODE_PASSWORD)
    
    dirs = [
        "D:\\VideoTranscode\\downloads\\long",
        "D:\\VideoTranscode\\downloads\\short",
    ]
    for d in dirs:
        ssh.exec_command(f'powershell -Command "New-Item -ItemType Directory -Path \'{d}\' -Force"')
        print(f"  创建: {d}")
    
    ssh.close()
    
    # 2. 主服务器目录
    print("\n2. 创建主服务器目录...")
    import subprocess
    dirs = [
        "/www/wwwroot/video-app/backend/uploads/shorts",
        "/www/wwwroot/video-app/backend/uploads/shorts/thumbnails",
        "/www/wwwroot/video-app/backend/uploads/shorts/previews",
    ]
    for d in dirs:
        cmd = f'ssh -i server_key_new -o StrictHostKeyChecking=no root@{MAIN_SERVER} "mkdir -p {d}"'
        subprocess.run(cmd, shell=True)
        print(f"  创建: {d}")
    
    print("\n完成!")
    print("\n目录结构:")
    print("  转码服务器:")
    print("    D:\\VideoTranscode\\downloads\\long\\   <- 放长视频")
    print("    D:\\VideoTranscode\\downloads\\short\\  <- 放短视频")
    print("  主服务器:")
    print("    /uploads/videos/      <- 长视频")
    print("    /uploads/shorts/      <- 短视频")

if __name__ == "__main__":
    main()
