#!/usr/bin/env python
"""添加小说表缺失的列"""
import asyncio
from sqlalchemy import text
import sys
sys.path.insert(0, '.')

from app.core.database import async_engine

async def migrate():
    async with async_engine.begin() as conn:
        # 添加 comment_count 列
        try:
            await conn.execute(text('ALTER TABLE novels ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0'))
            print('Added comment_count column to novels')
        except Exception as e:
            print(f'comment_count: {e}')
        
        # 添加 collect_count 列
        try:
            await conn.execute(text('ALTER TABLE novels ADD COLUMN IF NOT EXISTS collect_count INTEGER DEFAULT 0'))
            print('Added collect_count column to novels')
        except Exception as e:
            print(f'collect_count: {e}')
    
    print('Migration completed!')

if __name__ == '__main__':
    asyncio.run(migrate())
