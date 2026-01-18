#!/usr/bin/env python3
"""分析转码性能瓶颈"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

print("=" * 70)
print("转码服务器性能分析")
print("=" * 70)

# 1. CPU 信息
print("\n【1. CPU 信息】")
cmd = 'wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors /format:list'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
for line in output.strip().split('\n'):
    if line.strip() and '=' in line:
        print(f"   {line.strip()}")

# 2. 内存信息
print("\n【2. 内存信息】")
cmd = 'wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
for line in output.strip().split('\n'):
    if line.strip() and '=' in line:
        key, val = line.strip().split('=')
        if val:
            val_gb = int(val) / 1024 / 1024
            print(f"   {key}: {val_gb:.1f} GB")

# 3. GPU 信息
print("\n【3. GPU 信息】")
cmd = 'wmic path win32_VideoController get Name,AdapterRAM /format:list'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
for line in output.strip().split('\n'):
    if line.strip() and '=' in line:
        print(f"   {line.strip()}")

# 4. 检查 NVIDIA GPU
print("\n【4. NVIDIA GPU (nvidia-smi)】")
cmd = 'nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader 2>nul || echo "NVIDIA GPU not found or nvidia-smi not available"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(f"   {output.strip()}")

# 5. 当前 FFmpeg 配置
print("\n【5. 当前 FFmpeg 转码参数】")
cmd = 'powershell -Command "Select-String -Path D:\\VideoTranscode\\scripts\\watcher.ps1 -Pattern \'ffmpeg.*-c:v\' | Select-Object -First 3"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
print(output)

# 6. 磁盘速度测试
print("\n【6. 磁盘信息】")
cmd = 'wmic diskdrive get Model,Size,MediaType /format:list'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
for line in output.strip().split('\n'):
    if line.strip() and '=' in line:
        print(f"   {line.strip()}")

# 7. 网络带宽
print("\n【7. 网络适配器】")
cmd = 'wmic nic where "NetEnabled=true" get Name,Speed /format:list'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
output = stdout.read().decode('utf-8', errors='replace')
for line in output.strip().split('\n'):
    if line.strip() and '=' in line:
        print(f"   {line.strip()}")

ssh.close()
print("\n" + "=" * 70)
