#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广告和轮播图数据恢复脚本
创建基础的广告配置
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta

# 添加项目路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal


async def restore_ads():
    """恢复广告数据"""
    
    uploads_dir = os.path.join(backend_dir, 'uploads')
    images_dir = os.path.join(uploads_dir, 'images')
    
    print("=" * 50)
    print("广告数据恢复脚本")
    print("=" * 50)
    
    # 获取 images 目录中的图片
    images = []
    if os.path.exists(images_dir):
        for f in os.listdir(images_dir):
            if f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                images.append(f"/uploads/images/{f}")
    
    print(f"\n找到 {len(images)} 张图片")
    
    async with AsyncSessionLocal() as db:
        # 1. 创建轮播图 (取前5张图片)
        print("\n[1/4] 创建轮播图...")
        
        # 检查是否已有轮播图
        result = await db.execute(text("SELECT COUNT(*) FROM banners"))
        banner_count = result.scalar()
        
        if banner_count == 0:
            banner_images = images[:5] if len(images) >= 5 else images
            for i, img in enumerate(banner_images):
                await db.execute(
                    text("""
                        INSERT INTO banners (title, image_url, link_url, position, sort_order, is_active, created_at)
                        VALUES (:title, :image_url, :link_url, :position, :sort_order, 1, NOW())
                    """),
                    {
                        "title": f"轮播图 {i+1}",
                        "image_url": img,
                        "link_url": "/",
                        "position": "home",
                        "sort_order": i
                    }
                )
                print(f"  ✓ 创建轮播图 {i+1}")
            await db.commit()
        else:
            print(f"  - 已有 {banner_count} 个轮播图，跳过")
        
        # 2. 创建公告
        print("\n[2/4] 创建公告...")
        
        result = await db.execute(text("SELECT COUNT(*) FROM announcements"))
        if result.scalar() == 0:
            announcements = [
                ("欢迎使用Soul视频平台，最新最全的视频内容，尽在Soul平台！", "/"),
                ("VIP会员限时优惠，开通VIP享受更多精彩内容！", "/vip"),
            ]
            for i, (content, link) in enumerate(announcements):
                await db.execute(
                    text("""
                        INSERT INTO announcements (content, link, is_active, sort_order, created_at)
                        VALUES (:content, :link, 1, :sort_order, NOW())
                    """),
                    {"content": content, "link": link, "sort_order": i}
                )
                print(f"  ✓ 创建公告: {content[:20]}...")
            await db.commit()
        else:
            print("  - 已有公告，跳过")
        
        # 3. 创建功能入口
        print("\n[3/4] 创建功能入口...")
        
        result = await db.execute(text("SELECT COUNT(*) FROM func_entries"))
        if result.scalar() == 0:
            # func_entries 表结构: name, image, link, sort_order, is_active, click_count
            func_entries = [
                ("VIP会员", "/vip", 1),
                ("充值中心", "/recharge", 2),
                ("任务中心", "/tasks", 3),
                ("我的收藏", "/favorites", 4),
            ]
            for name, link, sort_order in func_entries:
                await db.execute(
                    text("""
                        INSERT INTO func_entries (name, link, sort_order, is_active, click_count, created_at)
                        VALUES (:name, :link, :sort_order, 1, 0, NOW())
                    """),
                    {"name": name, "link": link, "sort_order": sort_order}
                )
                print(f"  ✓ 创建功能入口: {name}")
            await db.commit()
        else:
            print("  - 已有功能入口，跳过")
        
        # 4. 统计
        print("\n[4/4] 恢复完成!")
        
        result = await db.execute(text("SELECT COUNT(*) FROM banners"))
        print(f"  - 轮播图: {result.scalar()} 个")
        
        result = await db.execute(text("SELECT COUNT(*) FROM announcements"))
        print(f"  - 公告: {result.scalar()} 条")
        
        result = await db.execute(text("SELECT COUNT(*) FROM func_entries"))
        print(f"  - 功能入口: {result.scalar()} 个")
    
    print("\n" + "=" * 50)
    print("广告数据恢复完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(restore_ads())

