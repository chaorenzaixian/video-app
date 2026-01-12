"""
设置主播头像 - 通用脚本
用法: python set_student_avatars.py <分类名> <文件前缀>
"""
import asyncio
import os
import sys
from PIL import Image
from sqlalchemy import text
from app.core.database import engine

# 默认参数
category = sys.argv[1] if len(sys.argv) > 1 else "人妻少妇"
file_prefix = sys.argv[2] if len(sys.argv) > 2 else "DM_20260109072241_"

async def set_avatars():
    upload_dir = "uploads/dating"
    
    # 获取所有PNG文件并按编号排序
    png_files = []
    for f in os.listdir(upload_dir):
        if f.endswith('.png') and file_prefix in f:
            num = int(f.split('_')[-1].replace('.png', ''))
            png_files.append((num, f))
    
    png_files.sort(key=lambda x: x[0])
    print(f"找到 {len(png_files)} 个PNG文件")
    
    # 获取指定分类的主播
    async with engine.begin() as conn:
        result = await conn.execute(text(f"SELECT id FROM dating_hosts WHERE sub_category = '{category}' ORDER BY sort_order"))
        hosts = result.fetchall()
        print(f"找到 {len(hosts)} 个{category}主播")
        
        # 按顺序分配头像
        for i, (host_id,) in enumerate(hosts):
            if i >= len(png_files):
                print(f"图片不够，主播 {host_id} 没有分配头像")
                continue
            
            num, png_file = png_files[i]
            png_path = os.path.join(upload_dir, png_file)
            webp_filename = f"host_avatar_{host_id}.webp"
            webp_path = os.path.join(upload_dir, webp_filename)
            
            try:
                img = Image.open(png_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(webp_path, 'WEBP', quality=85)
                print(f"转换: {png_file} -> {webp_filename}")
                
                avatar_url = f"/uploads/dating/{webp_filename}"
                await conn.execute(text(
                    "UPDATE dating_hosts SET avatar = :avatar WHERE id = :id"
                ), {"avatar": avatar_url, "id": host_id})
                
            except Exception as e:
                print(f"处理 {png_file} 失败: {e}")
        
        print(f"{category}头像设置完成!")

if __name__ == "__main__":
    asyncio.run(set_avatars())
