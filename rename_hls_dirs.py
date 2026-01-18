#!/usr/bin/env python3
"""重命名中文HLS目录为视频ID"""
import subprocess

# 视频ID和对应的中文目录名映射（从之前的检查结果）
# 需要手动匹配，因为中文目录名和视频标题可能不完全一致
mappings = [
    (111, "极品白虎少萝，户外尿急只能用刚喝完的矿泉水接尿，白虎小穴肉眼可见的嫩"),
    (119, "和长腿女神一起沐浴，骚逼痒得受不了一直在我身上摩擦，最后被后入爆操1"),
    (120, "和长腿女神一起沐浴，骚逼痒得受不了一直在我身上摩擦，最后被后入爆操2"),
    (124, "极品身材JK萝莉少女，鸡吧已经无法满足了，只能用拳头奖励她了"),
    (134, "Zoey 推特福利姬，户外露出，地下室停车场被金主调教"),
    (135, "唐伯虎 爆操极品美女小姐姐，白丝袜包裹着白虎穴，肌肤嫩滑如玉，全身散发着青春气息"),
    (136, "在落地窗前抱操极品女神，女上插入，后入爆操，猛烈冲击"),
    (137, "尾随白丝洛丽塔少萝宝宝回家，最后把她按在落地窗前爆操，连连求饶"),
    (138, "推特福利姬三岁小宝宝 巨乳萝莉cos流萤双人啪啪，口交吃鸡吧，被爆操"),
    (139, "猫屋少女，翘起可爱小屁屁让主人爸爸后入小蜜穴，超极品合法小母狗！"),
    (140, "身材极品的小美女，没想到在宿舍玩的这么花"),
]

print("=== 重命名中文HLS目录 ===")

# 先列出所有中文目录
print("\n当前中文目录:")
list_cmd = 'ls /www/wwwroot/video-app/backend/uploads/hls/ | grep -v "^[0-9]*$" | head -20'
result = subprocess.run(
    ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
     'root@38.47.218.137', list_cmd],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)

# 执行重命名
print("\n开始重命名...")
for vid, cn_name in mappings:
    # 尝试多种可能的目录名格式
    possible_names = [
        cn_name,
        cn_name.replace(" ", ""),  # 去掉空格
        cn_name.split("，")[0],    # 只取逗号前的部分
    ]
    
    for name in possible_names:
        # 检查目录是否存在
        check_cmd = f'test -d "/www/wwwroot/video-app/backend/uploads/hls/{name}" && echo "EXISTS" || echo "MISSING"'
        result = subprocess.run(
            ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
             'root@38.47.218.137', check_cmd],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        
        if result.stdout.strip() == "EXISTS":
            print(f"\n视频 {vid}: 找到目录 '{name[:30]}...'")
            # 重命名
            rename_cmd = f'mv "/www/wwwroot/video-app/backend/uploads/hls/{name}" "/www/wwwroot/video-app/backend/uploads/hls/{vid}" && echo "SUCCESS" || echo "FAILED"'
            result = subprocess.run(
                ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
                 'root@38.47.218.137', rename_cmd],
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            print(f"  重命名结果: {result.stdout.strip()}")
            break
    else:
        print(f"\n视频 {vid}: 未找到匹配的中文目录")

print("\n=== 验证结果 ===")
# 检查ID目录是否存在
for vid, _ in mappings:
    check_cmd = f'test -d /www/wwwroot/video-app/backend/uploads/hls/{vid} && echo "EXISTS" || echo "MISSING"'
    result = subprocess.run(
        ['ssh', '-i', 'server_key_new', '-o', 'StrictHostKeyChecking=no', 
         'root@38.47.218.137', check_cmd],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    status = "✓" if result.stdout.strip() == "EXISTS" else "✗"
    print(f"  {status} 视频 {vid}: /uploads/hls/{vid}/")
