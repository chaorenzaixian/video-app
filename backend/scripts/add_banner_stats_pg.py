#!/usr/bin/env python3
"""Add stats columns to banners table in PostgreSQL"""
import asyncio
import asyncpg

async def add_columns():
    conn = await asyncpg.connect('postgresql://video_app:VideoApp2024!@127.0.0.1:5432/video_app')
    
    # Add impression_count column
    try:
        await conn.execute('ALTER TABLE banners ADD COLUMN IF NOT EXISTS impression_count INTEGER DEFAULT 0')
        print('impression_count column added')
    except Exception as e:
        print(f'impression_count error: {e}')
    
    # Add click_count column
    try:
        await conn.execute('ALTER TABLE banners ADD COLUMN IF NOT EXISTS click_count INTEGER DEFAULT 0')
        print('click_count column added')
    except Exception as e:
        print(f'click_count error: {e}')
    
    await conn.close()
    print('Migration completed')

if __name__ == '__main__':
    asyncio.run(add_columns())
