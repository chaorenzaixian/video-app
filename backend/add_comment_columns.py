"""
添加评论表新字段
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_columns():
    async with engine.begin() as conn:
        # 添加 image_url 列
        try:
            await conn.execute(text('ALTER TABLE comments ADD COLUMN image_url VARCHAR(500)'))
            print('Added image_url column')
        except Exception as e:
            print(f'image_url column may already exist: {e}')
        
        # 添加 is_official 列
        try:
            await conn.execute(text('ALTER TABLE comments ADD COLUMN is_official BOOLEAN DEFAULT FALSE'))
            print('Added is_official column')
        except Exception as e:
            print(f'is_official column may already exist: {e}')
    
    print('Done!')

if __name__ == "__main__":
    asyncio.run(add_columns())




