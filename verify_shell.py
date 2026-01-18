#!/usr/bin/env python3
"""使用shell验证文件"""
import paramiko

TRANSCODE_HOST = '198.176.60.121'
TRANSCODE_USER = 'Administrator'
TRANSCODE_PASS = 'jCkMIjNlnSd7f6GM'
MAIN_HOST = '38.47.218.137'
MAIN_KEY = 'C:\\server_key'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(TRANSCODE_HOST, username=TRANSCODE_USER, password=TRANSCODE_PASS, timeout=60)

# 使用shell命令验证
print("验证视频文件...")

videos = [
    (102, '萝莉 (8)'),
    (103, '萝莉'),
    (104, '和长腿女神一起沐浴，骚逼痒得受不了一直在我身上摩擦，最后被后入爆操'),
    (105, '大吉大利～新的一年祝我吃到更多的鸡吧，清纯颜值小嫩妹给你口交'),
    (106, '极品白虎少萝，户外尿急只能用刚喝完的矿泉水接尿，白虎小穴肉眼可见的嫩'),
    (107, '穿着小白袜的学妹，躲在卧室看黄片，结果被我发现了，被我狠狠的调教，顶级神仙身材，还是个小白虎'),
    (108, '身材极品的小美女，没想到在宿舍玩的这么花'),
]

for video_id, title in videos:
    print(f"\n视频 {video_id}: {title[:30]}...")
    
    # 检查HLS
    cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "test -f \\"/www/wwwroot/video-app/backend/uploads/hls/{title}/master.m3u8\\" && echo HLS_OK || echo HLS_MISSING"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(f"  HLS: {stdout.read().decode('utf-8').strip()}")
    
    # 检查封面
    cmd = f'ssh -i {MAIN_KEY} -o StrictHostKeyChecking=no root@{MAIN_HOST} "test -f \\"/www/wwwroot/video-app/backend/uploads/thumbnails/{title}.webp\\" && echo COVER_OK || echo COVER_MISSING"'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(f"  封面: {stdout.read().decode('utf-8').strip()}")

ssh.close()
