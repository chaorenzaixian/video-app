#!/usr/bin/env python3
"""为 PostgreSQL 数据库的 banners 表添加统计字段"""
import asyncio
import asyncpg

async def add_columns():
    conn = await asyncpg.connect('postgresql://video_app:VideoApp2024!@127.0.0.1:5432/video_app')
    
    # 检查并添加 impression_count 列
    try:
        await conn.execute('ALTER TABLE banners ADD COLUMN IF NOT EXISTS impression_count INTEGER DEFAULT 0')
        print('impression_count 列添加成功')
    except Exception as e:
        print(f'impression_count: {e}')
    
    # 检查并添加 click_count 列
    try:
        await conn.execute('ALTER TABLE banners ADD COLUMN IF NOT EXISTS click_count INTEGER DEFAULT 0')
        print('click_count 列添加成功')
    except Exception as e:
        print(f'click_count: {e}')
    
    await conn.close()
    print('数据库迁移完成')

if __name__ == '__main__':
    asyncio.run(add_columns())
