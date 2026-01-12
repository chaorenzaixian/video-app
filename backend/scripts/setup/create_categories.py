#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量创建普通视频分类
运行方式: python create_categories.py
"""
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

import asyncio

# 要创建的分类列表
CATEGORIES = [
    "国产",
    "17岁",
    "AV",
    "动漫",
    "漫画",
    "黑料",
    "制服",
    "猎奇",
    "原创",
    "直播",
    "网黄",
    "欧美",
    "韩国",
    "综艺",
]

async def create_categories():
    from app.core.database import AsyncSessionLocal
    from app.models.video import VideoCategory
    from sqlalchemy import select
    
    print("=" * 50)
    print("批量创建普通视频分类")
    print("=" * 50)
    
    async with AsyncSessionLocal() as db:
        created = 0
        skipped = 0
        
        for i, name in enumerate(CATEGORIES, 1):
            # 检查是否已存在
            result = await db.execute(
                select(VideoCategory).where(VideoCategory.name == name)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"[跳过] {name} - 已存在 (ID: {existing.id})")
                skipped += 1
                continue
            
            # 创建新分类
            category = VideoCategory(
                name=name,
                description=f"{name}分类",
                sort_order=i * 10,  # 排序：10, 20, 30...
                is_active=True,
                category_type="video"  # 普通视频分类
            )
            
            db.add(category)
            print(f"[创建] {name}")
            created += 1
        
        await db.commit()
        
        print("=" * 50)
        print(f"完成！创建: {created} 个，跳过: {skipped} 个")
        print("=" * 50)
        
        # 显示所有分类
        print("\n当前所有普通视频分类:")
        result = await db.execute(
            select(VideoCategory).where(
                VideoCategory.category_type == "video"
            ).order_by(VideoCategory.sort_order)
        )
        categories = result.scalars().all()
        for cat in categories:
            print(f"  ID: {cat.id:3} | {cat.name}")

if __name__ == "__main__":
    # 兼容旧版本 Python
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_categories())

