"""
批量设置群聊头像 - 将PNG转换为WebP并更新数据库
"""
import asyncio
import os
from PIL import Image
from sqlalchemy import text
from app.core.database import engine

async def batch_set_avatars():
    upload_dir = "uploads/dating"
    
    # 获取所有PNG文件并按编号排序
    png_files = []
    for f in os.listdir(upload_dir):
        if f.endswith('.png') and 'DM_20260109062348_' in f:
            # 提取编号
            num = int(f.split('_')[-1].replace('.png', ''))
            png_files.append((num, f))
    
    png_files.sort(key=lambda x: x[0])
    print(f"找到 {len(png_files)} 个PNG文件")
    
    # 获取所有群聊
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id FROM dating_groups ORDER BY sort_order"))
        groups = result.fetchall()
        print(f"找到 {len(groups)} 个群聊")
        
        # 按顺序分配头像
        for i, (group_id,) in enumerate(groups):
            if i >= len(png_files):
                print(f"图片不够，群聊 {group_id} 没有分配头像")
                continue
            
            num, png_file = png_files[i]
            png_path = os.path.join(upload_dir, png_file)
            webp_filename = f"group_avatar_{group_id}.webp"
            webp_path = os.path.join(upload_dir, webp_filename)
            
            # 转换为webp
            try:
                img = Image.open(png_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(webp_path, 'WEBP', quality=85)
                print(f"转换: {png_file} -> {webp_filename}")
                
                # 更新数据库
                avatar_url = f"/uploads/dating/{webp_filename}"
                await conn.execute(text(
                    "UPDATE dating_groups SET avatar = :avatar WHERE id = :id"
                ), {"avatar": avatar_url, "id": group_id})
                
            except Exception as e:
                print(f"处理 {png_file} 失败: {e}")
        
        print("批量设置头像完成!")

if __name__ == "__main__":
    asyncio.run(batch_set_avatars())
