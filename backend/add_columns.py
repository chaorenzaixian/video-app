"""添加用户表字段"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_columns():
    async with engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE users ADD COLUMN device_id VARCHAR(100) UNIQUE'))
            print('✓ Added device_id column')
        except Exception as e:
            if 'already exists' in str(e) or '已经存在' in str(e):
                print('✓ device_id column already exists')
            else:
                print(f'✗ device_id error: {e}')
        
        try:
            await conn.execute(text('ALTER TABLE users ADD COLUMN is_guest BOOLEAN DEFAULT FALSE'))
            print('✓ Added is_guest column')
        except Exception as e:
            if 'already exists' in str(e) or '已经存在' in str(e):
                print('✓ is_guest column already exists')
            else:
                print(f'✗ is_guest error: {e}')

if __name__ == '__main__':
    asyncio.run(add_columns())
    print('Done!')





