#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频数据恢复脚本
扫描 uploads 目录中的视频文件，自动恢复到数据库
"""
import os
import sys
import asyncio
from datetime import datetime

# 添加项目路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal


async def get_video_duration_from_m3u8(m3u8_path):
    """从 m3u8 文件估算视频时长"""
    try:
        total_duration = 0
        with open(m3u8_path, 'r') as f:
            for line in f:
                if line.startswith('#EXTINF:'):
                    # 格式: #EXTINF:10.000000,
                    duration_str = line.split(':')[1].split(',')[0]
                    total_duration += float(duration_str)
        return total_duration
    except:
        return 0


async def restore_videos():
    """恢复视频数据"""
    
    uploads_dir = os.path.join(backend_dir, 'uploads')
    hls_dir = os.path.join(uploads_dir, 'hls')
    thumbnails_dir = os.path.join(uploads_dir, 'thumbnails')
    
    print("=" * 50)
    print("视频数据恢复脚本")
    print("=" * 50)
    
    # 获取所有 HLS 目录
    hls_folders = []
    if os.path.exists(hls_dir):
        for folder in os.listdir(hls_dir):
            folder_path = os.path.join(hls_dir, folder)
            if os.path.isdir(folder_path):
                m3u8_path = os.path.join(folder_path, 'playlist.m3u8')
                if os.path.exists(m3u8_path):
                    hls_folders.append(folder)
    
    print(f"\n找到 {len(hls_folders)} 个 HLS 视频目录")
    
    if not hls_folders:
        print("没有找到可恢复的视频！")
        return
    
    async with AsyncSessionLocal() as db:
        # 1. 先创建默认分类
        print("\n[1/3] 创建视频分类...")
        categories = [
            ("热门推荐", "最热门的精选视频", 1, True),
            ("最新上传", "最新上传的视频", 2, True),
            ("精选视频", "精心挑选的优质内容", 3, True),
            ("VIP专区", "VIP会员专享内容", 4, False),
        ]
        
        for name, desc, sort_order, is_featured in categories:
            # 检查是否已存在
            result = await db.execute(
                text("SELECT id FROM video_categories WHERE name = :name"),
                {"name": name}
            )
            if not result.scalar():
                await db.execute(
                    text("""
                        INSERT INTO video_categories (name, description, sort_order, is_active, is_featured, category_type, level)
                        VALUES (:name, :desc, :sort_order, 1, :is_featured, 'video', 1)
                    """),
                    {"name": name, "desc": desc, "sort_order": sort_order, "is_featured": is_featured}
                )
                print(f"  ✓ 创建分类: {name}")
        
        await db.commit()
        
        # 获取第一个分类ID
        result = await db.execute(text("SELECT id FROM video_categories ORDER BY sort_order LIMIT 1"))
        default_category_id = result.scalar() or 1
        
        # 2. 恢复视频记录
        print("\n[2/3] 恢复视频记录...")
        
        restored_count = 0
        for folder in sorted(hls_folders, key=lambda x: int(x) if x.isdigit() else 0):
            video_id = int(folder) if folder.isdigit() else None
            if not video_id:
                continue
            
            # 检查是否已存在
            result = await db.execute(
                text("SELECT id FROM videos WHERE id = :id"),
                {"id": video_id}
            )
            if result.scalar():
                print(f"  - 视频 ID {video_id} 已存在，跳过")
                continue
            
            # 构建路径
            hls_url = f"/uploads/hls/{folder}/playlist.m3u8"
            m3u8_path = os.path.join(hls_dir, folder, 'playlist.m3u8')
            
            # 查找缩略图
            cover_url = None
            for ext in ['.jpg', '.webp', '.png']:
                thumb_file = f"{folder}{ext}"
                if os.path.exists(os.path.join(thumbnails_dir, thumb_file)):
                    cover_url = f"/uploads/thumbnails/{thumb_file}"
                    break
            
            # 获取时长
            duration = await get_video_duration_from_m3u8(m3u8_path)
            
            # 生成标题
            title = f"视频 {video_id}"
            
            # 插入视频记录
            await db.execute(
                text("""
                    INSERT INTO videos (
                        id, title, description, cover_url, hls_url, duration,
                        status, quality, is_vip_only, is_featured, is_short,
                        pay_type, coin_price, vip_coin_price, 
                        view_count, like_count, favorite_count, comment_count, share_count,
                        category_id, uploader_id, created_at, updated_at, published_at
                    ) VALUES (
                        :id, :title, :description, :cover_url, :hls_url, :duration,
                        'PUBLISHED', 'HD', 0, 0, 0,
                        'free', 0, 0,
                        0, 0, 0, 0, 0,
                        :category_id, 1, NOW(), NOW(), NOW()
                    )
                """),
                {
                    "id": video_id,
                    "title": title,
                    "description": f"视频 {video_id} 的描述",
                    "cover_url": cover_url,
                    "hls_url": hls_url,
                    "duration": duration,
                    "category_id": default_category_id
                }
            )
            restored_count += 1
            print(f"  ✓ 恢复视频 ID {video_id}: {title} (时长: {duration:.1f}秒)")
        
        await db.commit()
        
        # 3. 显示统计
        print("\n[3/3] 恢复完成!")
        print(f"  - 成功恢复 {restored_count} 个视频")
        
        # 查询总数
        result = await db.execute(text("SELECT COUNT(*) FROM videos"))
        total_videos = result.scalar()
        result = await db.execute(text("SELECT COUNT(*) FROM video_categories"))
        total_categories = result.scalar()
        
        print(f"  - 视频总数: {total_videos}")
        print(f"  - 分类总数: {total_categories}")
    
    print("\n" + "=" * 50)
    print("恢复完成! 请刷新前端页面查看效果。")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(restore_videos())




