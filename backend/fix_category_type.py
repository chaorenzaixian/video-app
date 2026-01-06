#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复视频分类的 category_type 字段
运行方式: python fix_category_type.py
"""
import os
import sys

# 确保当前目录是 backend 目录
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

import asyncio
from sqlalchemy import text

async def fix_category_type():
    from app.core.database import AsyncSessionLocal
    
    print("[*] 检查并修复视频分类的 category_type 字段...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 检查 category_type 列是否存在
            try:
                result = await db.execute(text(
                    "SELECT category_type FROM video_categories LIMIT 1"
                ))
                print("[OK] category_type 列已存在")
            except Exception as e:
                print(f"[!] category_type 列不存在，尝试添加...")
                try:
                    await db.execute(text(
                        "ALTER TABLE video_categories ADD COLUMN category_type VARCHAR(20) DEFAULT 'video'"
                    ))
                    await db.commit()
                    print("[OK] category_type 列添加成功")
                except Exception as add_err:
                    print(f"[ERROR] 添加列失败: {add_err}")
                    return
            
            # 获取所有分类
            result = await db.execute(text(
                "SELECT id, name, category_type FROM video_categories ORDER BY id"
            ))
            categories = result.fetchall()
            
            print(f"\n当前分类列表 ({len(categories)} 条):")
            print("-" * 60)
            for cat in categories:
                cat_type = cat[2] if cat[2] else 'NULL'
                print(f"  ID: {cat[0]:3} | 名称: {cat[1]:20} | 类型: {cat_type}")
            
            # 将所有 NULL 的 category_type 设置为 'video'
            update_result = await db.execute(text(
                "UPDATE video_categories SET category_type = 'video' WHERE category_type IS NULL OR category_type = ''"
            ))
            await db.commit()
            
            affected = update_result.rowcount
            if affected > 0:
                print(f"\n[OK] 已将 {affected} 个分类的类型设置为 'video'")
            else:
                print("\n[OK] 所有分类的 category_type 已正确设置")
            
            # 显示修复后的结果
            result = await db.execute(text(
                "SELECT id, name, category_type FROM video_categories ORDER BY id"
            ))
            categories = result.fetchall()
            
            print(f"\n修复后的分类列表:")
            print("-" * 60)
            for cat in categories:
                cat_type = cat[2] if cat[2] else 'NULL'
                print(f"  ID: {cat[0]:3} | 名称: {cat[1]:20} | 类型: {cat_type}")
                
        except Exception as e:
            print(f"[ERROR] 发生错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_category_type())
    print("\n[DONE] 完成")


