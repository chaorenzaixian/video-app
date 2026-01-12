#!/usr/bin/env python
"""添加小说、图集和帖子表缺失的列"""
import asyncio
from sqlalchemy import text
import sys
sys.path.insert(0, '.')

from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # novels 表
        try:
            await conn.execute(text('ALTER TABLE novels ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0'))
            print('Added comment_count column to novels')
        except Exception as e:
            print(f'novels.comment_count: {e}')
        
        try:
            await conn.execute(text('ALTER TABLE novels ADD COLUMN IF NOT EXISTS collect_count INTEGER DEFAULT 0'))
            print('Added collect_count column to novels')
        except Exception as e:
            print(f'novels.collect_count: {e}')
        
        # galleries 表
        try:
            await conn.execute(text('ALTER TABLE galleries ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0'))
            print('Added comment_count column to galleries')
        except Exception as e:
            print(f'galleries.comment_count: {e}')
        
        try:
            await conn.execute(text('ALTER TABLE galleries ADD COLUMN IF NOT EXISTS collect_count INTEGER DEFAULT 0'))
            print('Added collect_count column to galleries')
        except Exception as e:
            print(f'galleries.collect_count: {e}')
        
        # posts 表
        try:
            await conn.execute(text('ALTER TABLE posts ADD COLUMN IF NOT EXISTS collect_count INTEGER DEFAULT 0'))
            print('Added collect_count column to posts')
        except Exception as e:
            print(f'posts.collect_count: {e}')
    
    print('Migration completed!')

if __name__ == '__main__':
    asyncio.run(migrate())
