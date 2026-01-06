#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断视频分类问题
运行方式: python diagnose_categories.py
"""
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

import asyncio

async def diagnose():
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text
    
    print("=" * 60)
    print("视频分类诊断")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # 1. 检查表结构
        print("\n[1] 检查 video_categories 表结构:")
        try:
            # MySQL
            result = await db.execute(text(
                "DESCRIBE video_categories"
            ))
            columns = result.fetchall()
            print("  列名 | 类型 | 是否可空 | 默认值")
            print("  " + "-" * 50)
            for col in columns:
                print(f"  {col[0]:20} | {col[1]:15} | {col[2]:5} | {col[4]}")
        except Exception as e:
            print(f"  错误: {e}")
            # SQLite
            try:
                result = await db.execute(text("PRAGMA table_info(video_categories)"))
                columns = result.fetchall()
                for col in columns:
                    print(f"  {col[1]:20} | {col[2]:15} | notnull={col[3]} | default={col[4]}")
            except Exception as e2:
                print(f"  SQLite 也失败: {e2}")
        
        # 2. 检查所有分类数据
        print("\n[2] 所有分类数据:")
        try:
            result = await db.execute(text(
                "SELECT id, name, is_active, category_type FROM video_categories ORDER BY id"
            ))
            categories = result.fetchall()
            print(f"  共 {len(categories)} 条记录")
            print("  ID | 名称 | 激活 | 分类类型")
            print("  " + "-" * 50)
            for cat in categories:
                cat_type = cat[3] if cat[3] else 'NULL'
                is_active = '是' if cat[1] else '否'
                print(f"  {cat[0]:3} | {cat[1]:20} | {cat[2]} | {cat_type}")
        except Exception as e:
            print(f"  错误: {e}")
        
        # 3. 检查 video 类型的分类
        print("\n[3] category_type='video' 或 'both' 的分类:")
        try:
            result = await db.execute(text(
                "SELECT id, name, category_type FROM video_categories WHERE is_active = 1 AND (category_type = 'video' OR category_type = 'both')"
            ))
            categories = result.fetchall()
            print(f"  找到 {len(categories)} 条")
            for cat in categories:
                print(f"  ID={cat[0]}, 名称={cat[1]}, 类型={cat[2]}")
        except Exception as e:
            print(f"  错误: {e}")
        
        # 4. 修复 NULL 的 category_type
        print("\n[4] 尝试修复 NULL 的 category_type:")
        try:
            result = await db.execute(text(
                "UPDATE video_categories SET category_type = 'video' WHERE category_type IS NULL OR category_type = ''"
            ))
            await db.commit()
            print(f"  已修复 {result.rowcount} 条记录")
        except Exception as e:
            print(f"  修复失败: {e}")
        
        # 5. 再次检查
        print("\n[5] 修复后的分类:")
        try:
            result = await db.execute(text(
                "SELECT id, name, is_active, category_type FROM video_categories ORDER BY id"
            ))
            categories = result.fetchall()
            for cat in categories:
                cat_type = cat[3] if cat[3] else 'NULL'
                print(f"  ID={cat[0]:3}, 名称={cat[1]:20}, 激活={cat[2]}, 类型={cat_type}")
        except Exception as e:
            print(f"  错误: {e}")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(diagnose())


