#!/usr/bin/env python3
"""验证视频播放"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 检查视频文件是否存在
print("检查视频文件...")

videos = [
    ('萝莉 (8)', 102),
    ('萝莉', 103),
    ('和长腿女神一起沐浴，骚逼痒得受不了一直在我身上摩擦，最后被后入爆操', 104),
    ('大吉大利～新的一年祝我吃到更多的鸡吧，清纯颜值小嫩妹给你口交', 105),
    ('极品白虎少萝，户外尿急只能用刚喝完的矿泉水接尿，白虎小穴肉眼可见的嫩', 106),
    ('穿着小白袜的学妹，躲在卧室看黄片，结果被我发现了，被我狠狠的调教，顶级神仙身材，还是个小白虎', 107),
    ('身材极品的小美女，没想到在宿舍玩的这么花', 108),
]

for title, video_id in videos:
    print(f"\n视频 {video_id}: {title[:30]}...")
    
    # 检查HLS目录
    cmd = f'ls -la "/www/wwwroot/video-app/backend/uploads/hls/{title}/" 2>/dev/null | head -5 || echo "HLS目录不存在"'
    run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} \'{cmd}\''
    stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"  HLS: {output.strip()[:100]}")
    
    # 检查封面
    cmd = f'ls -la "/www/wwwroot/video-app/backend/uploads/thumbnails/{title}.webp" 2>/dev/null || echo "封面不存在"'
    run_cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} \'{cmd}\''
    stdin, stdout, stderr = ssh.exec_command(run_cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='replace')
    print(f"  封面: {output.strip()[:100]}")

# 检查数据库中的URL
print("\n\n数据库中的URL:")
cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "PGPASSWORD=\'VideoApp2024!\' psql -h localhost -U video_app -d video_app -c \'SELECT id, cover_url, hls_url FROM videos WHERE id >= 102 ORDER BY id;\'"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
