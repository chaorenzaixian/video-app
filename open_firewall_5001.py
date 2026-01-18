#!/usr/bin/env python3
"""开放转码服务器5001端口防火墙"""
import paramiko
import time

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'

print("连接转码服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=30)
print("✓ 已连接")

# 1. 检查当前防火墙规则
print("\n1. 检查现有防火墙规则...")
stdin, stdout, stderr = ssh.exec_command('netsh advfirewall firewall show rule name="Status API 5001"')
out = stdout.read().decode('gbk', errors='ignore')
print(out if out else "规则不存在")

# 2. 添加防火墙规则
print("\n2. 添加防火墙规则...")
# 删除旧规则（如果存在）
ssh.exec_command('netsh advfirewall firewall delete rule name="Status API 5001"')
time.sleep(1)

# 添加入站规则
add_rule_cmd = 'netsh advfirewall firewall add rule name="Status API 5001" dir=in action=allow protocol=tcp localport=5001'
stdin, stdout, stderr = ssh.exec_command(add_rule_cmd)
out = stdout.read().decode('gbk', errors='ignore')
err = stderr.read().decode('gbk', errors='ignore')
print(f"输出: {out}")
if err:
    print(f"错误: {err}")

# 3. 验证规则已添加
print("\n3. 验证规则...")
stdin, stdout, stderr = ssh.exec_command('netsh advfirewall firewall show rule name="Status API 5001"')
print(stdout.read().decode('gbk', errors='ignore'))

# 4. 确认API仍在运行
print("\n4. 确认API运行状态...")
stdin, stdout, stderr = ssh.exec_command('netstat -ano | findstr :5001')
port = stdout.read().decode('gbk', errors='ignore')
print(port if port else "端口5001未监听")

# 5. 本地测试
print("\n5. 本地测试API...")
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:5001/health')
print(f"响应: {stdout.read().decode()}")

ssh.close()
print("\n防火墙配置完成")
