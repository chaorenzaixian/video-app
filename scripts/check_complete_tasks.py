import paramiko
import os
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('198.176.60.121', username='Administrator', password='jCkMIjNlnSd7f6GM')

# 列出processing目录
stdin, stdout, stderr = ssh.exec_command('dir /b D:\\VideoTranscode\\processing')
dirs = stdout.read().decode('gbk', errors='ignore').strip().split('\n')
print(f'Total processing dirs: {len(dirs)}')

complete = []
incomplete = []

for d in dirs:
    d = d.strip()
    if not d:
        continue
    # 检查是否有hls和covers目录
    stdin, stdout, stderr = ssh.exec_command(f'if exist D:\\VideoTranscode\\processing\\{d}\\hls\\master.m3u8 (echo HLS_OK) else (echo NO_HLS)')
    hls_ok = 'HLS_OK' in stdout.read().decode()
    
    stdin, stdout, stderr = ssh.exec_command(f'if exist D:\\VideoTranscode\\processing\\{d}\\covers\\cover_1.webp (echo COVERS_OK) else (echo NO_COVERS)')
    covers_ok = 'COVERS_OK' in stdout.read().decode()
    
    if hls_ok and covers_ok:
        complete.append(d)
    else:
        incomplete.append((d, hls_ok, covers_ok))

print(f'\nComplete tasks (HLS + Covers): {len(complete)}')
print(f'Incomplete tasks: {len(incomplete)}')

if incomplete[:5]:
    print('\nFirst 5 incomplete:')
    for d, hls, covers in incomplete[:5]:
        print(f'  {d}: HLS={hls}, Covers={covers}')

ssh.close()
