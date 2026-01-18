#!/usr/bin/env python3
"""Quick test of the workflow"""
import paramiko
import time

SERVER = "198.176.60.121"
USER = "Administrator"
PASSWORD = "jCkMIjNlnSd7f6GM"

def quick_test():
    print("=" * 50)
    print("Quick Workflow Test")
    print("=" * 50)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
        print("✓ Connected to transcode server")
        
        # Copy existing file to trigger processing
        print("\nStep 1: Creating test file...")
        copy_cmd = 'copy D:\\VideoTranscode\\completed\\test2_transcoded.mp4 D:\\VideoTranscode\\downloads\\test_new.mp4'
        stdin, stdout, stderr = ssh.exec_command(copy_cmd)
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print("✓ Test file created: test_new.mp4")
        else:
            print("✗ Failed to create test file")
            return False
        
        print("\nStep 2: Monitoring processing (30 seconds)...")
        
        for i in range(6):  # Check every 5 seconds for 30 seconds
            time.sleep(5)
            
            # Check if file is being processed
            stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\downloads\\test_new.mp4 2>nul')
            in_downloads = stdout.channel.recv_exit_status() == 0
            
            stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\processing\\test_new.mp4 2>nul')
            in_processing = stdout.channel.recv_exit_status() == 0
            
            stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\test_new_transcoded.mp4 2>nul')
            in_completed = stdout.channel.recv_exit_status() == 0
            
            if in_downloads:
                print(f"  [{(i+1)*5}s] File still in downloads...")
            elif in_processing:
                print(f"  [{(i+1)*5}s] File is being processed...")
            elif in_completed:
                print(f"  [{(i+1)*5}s] ✓ Processing completed!")
                break
            else:
                print(f"  [{(i+1)*5}s] File processed or moved...")
        
        # Check final result
        print("\nStep 3: Checking results...")
        
        # Check completed file
        stdin, stdout, stderr = ssh.exec_command('dir D:\\VideoTranscode\\completed\\test_new_transcoded.mp4')
        if stdout.channel.recv_exit_status() == 0:
            print("✓ Transcoded file exists")
        else:
            print("✗ Transcoded file not found")
        
        # Check recent logs
        stdin, stdout, stderr = ssh.exec_command('powershell "Get-Content D:\\VideoTranscode\\logs\\watcher.log -Tail 10"')
        logs = stdout.read().decode('utf-8', errors='ignore')
        if logs:
            print("\nRecent watcher logs:")
            print(logs)
        
        # Check upload logs
        stdin, stdout, stderr = ssh.exec_command('powershell "Get-Content D:\\VideoTranscode\\logs\\upload.log -Tail 5"')
        upload_logs = stdout.read().decode('utf-8', errors='ignore')
        if upload_logs:
            print("\nRecent upload logs:")
            print(upload_logs)
        
        ssh.close()
        
        print("\n" + "=" * 50)
        print("Test completed!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    quick_test()