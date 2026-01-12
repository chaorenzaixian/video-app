"""修复前端代码中的 .png 引用为 .webp"""
import os
import re

# 需要替换的文件列表
png_files = [
    "mine_notification",
    "publish", 
    "publish_video",
    "app_dlbtw",
    "app_dlbtw2",
    "app_dlcy",
    "app_proxy_btn_bg",
    "app_mine_jelly_share_qr_bg-Photoroom",
    "app_share_up_bg",
    "msg_button",
    "wallet_coin_bg_1",
    "mine_withdraw_sel",
    "下载 (4)",
    "下载 (5)",
]

def fix_file(filepath):
    """修复单个文件中的引用"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 替换背景图片
        for png_file in png_files:
            content = content.replace(f'{png_file}.png', f'{png_file}.webp')
        
        # 替换头像引用 - 各种模式
        # 模式1: icon_avatar_${index + 1}.png
        content = re.sub(
            r'icon_avatar_\$\{[^}]+\}\.png',
            lambda m: m.group(0).replace('.png', '.webp'),
            content
        )
        # 模式2: icon_avatar_${i}.png
        content = re.sub(
            r'icon_avatar_\$\{i\}\.png',
            'icon_avatar_${i}.webp',
            content
        )
        # 模式3: icon_avatar_1.png (固定数字)
        content = re.sub(
            r"icon_avatar_(\d+)\.png",
            r"icon_avatar_\1.webp",
            content
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✅ 修复: {filepath}')
            return True
        return False
    except Exception as e:
        print(f'❌ 错误 {filepath}: {e}')
        return False

# 遍历前端源码目录
count = 0
for root, dirs, files in os.walk('frontend/src'):
    dirs[:] = [d for d in dirs if d not in {'node_modules', '.git'}]
    for file in files:
        if file.endswith(('.vue', '.js', '.ts', '.css', '.scss')):
            filepath = os.path.join(root, file)
            if fix_file(filepath):
                count += 1

print(f'\n共修复 {count} 个文件')
