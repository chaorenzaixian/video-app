#!/usr/bin/env python3
"""Auto deploy files to transcode server"""
import os
import sys

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    os.system("pip install paramiko")
    import paramiko

# Server config
SERVER = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

# Files to deploy
FILES = [
    ("deploy_files/upload_simple.py", "D:/VideoTranscode/scripts/upload_simple.py"),
    ("deploy_files/upload_to_main.ps1", "D:/VideoTranscode/scripts/upload_to_main.ps1"),
    ("deploy_files/watcher.ps1", "D:/VideoTranscode/scripts/watcher.ps1"),
]

def deploy():
    print("=" * 60)
    print("Auto Deploy to Transcode Server")
    print("=" * 60)
    print()
    
    try:
        # Connect
        print(f"Connecting to {SERVER}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
        print("✓ Connected")
        print()
        
        # Create SFTP client
        sftp = ssh.open_sftp()
        
        # Upload files
        print("Uploading files...")
        for local_file, remote_file in FILES:
            if not os.path.exists(local_file):
                print(f"✗ File not found: {local_file}")
                continue
            
            print(f"  {local_file} -> {remote_file}")
            
            # Convert Windows path to Unix-style for SFTP
            remote_file_unix = remote_file.replace("\\", "/")
            
            try:
                sftp.put(local_file, remote_file_unix)
                print(f"    ✓ Uploaded")
            except Exception as e:
                print(f"    ✗ Failed: {e}")
        
        print()
        
        # Install paramiko on remote server
        print("Installing paramiko on transcode server...")
        stdin, stdout, stderr = ssh.exec_command("python -m pip install paramiko")
        stdout.channel.recv_exit_status()  # Wait for command to complete
        print("✓ Paramiko installed")
        print()
        
        # Test upload script
        print("Testing upload script...")
        test_cmd = "python D:\\VideoTranscode\\scripts\\upload_simple.py D:\\VideoTranscode\\completed\\test2_transcoded.mp4"
        stdin, stdout, stderr = ssh.exec_command(test_cmd)
        
        # Print output
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output)
        if error:
            print("Errors:", error)
        
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("✓ Upload test successful!")
        else:
            print(f"✗ Upload test failed with exit code: {exit_code}")
        
        # Close connections
        sftp.close()
        ssh.close()
        
        print()
        print("=" * 60)
        print("Deployment Complete!")
        print("=" * 60)
        print()
        print("Next step: Start the watcher service on transcode server:")
        print("powershell -ExecutionPolicy Bypass -NoExit -File D:\\VideoTranscode\\scripts\\watcher.ps1")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)
