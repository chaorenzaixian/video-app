#!/usr/bin/env python3
"""Simple upload script using paramiko"""
import sys
import os
from datetime import datetime

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    os.system("pip install paramiko")
    import paramiko

def log_message(message, log_file="D:\\VideoTranscode\\logs\\upload.log"):
    """Write log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"{timestamp} - {message}"
    print(log_msg)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass

def upload_file(local_path, remote_host="38.47.218.137", remote_user="root", 
                remote_password="APnoPrlVoa1abrFJ", 
                remote_path="/www/wwwroot/video-app/backend/uploads/videos/"):
    """Upload file via SFTP"""
    
    log_message("=" * 50)
    log_message(f"Starting upload: {local_path}")
    
    if not os.path.exists(local_path):
        log_message(f"ERROR: File not found: {local_path}")
        return False
    
    file_name = os.path.basename(local_path)
    file_size = os.path.getsize(local_path) / (1024 * 1024)  # MB
    log_message(f"File: {file_name}")
    log_message(f"Size: {file_size:.2f} MB")
    
    log_message("Connecting to main server...")
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect
        start_time = datetime.now()
        ssh.connect(remote_host, username=remote_user, password=remote_password, timeout=30)
        
        # Create SFTP client
        sftp = ssh.open_sftp()
        
        log_message("Uploading...")
        
        # Upload file
        remote_file = remote_path + file_name
        sftp.put(local_path, remote_file)
        
        # Close connections
        sftp.close()
        ssh.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        speed = file_size / duration if duration > 0 else 0
        
        log_message("Upload successful!")
        log_message(f"Duration: {duration:.2f} seconds")
        log_message(f"Speed: {speed:.2f} MB/s")
        log_message(f"Remote path: {remote_host}:{remote_file}")
        log_message("=" * 50)
        
        return True
        
    except Exception as e:
        log_message(f"ERROR: Upload failed: {str(e)}")
        log_message("=" * 50)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_simple.py <video_file>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    success = upload_file(video_file)
    sys.exit(0 if success else 1)
