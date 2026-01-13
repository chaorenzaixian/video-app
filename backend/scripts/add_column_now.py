import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import text
from app.core.database import engine

async def add_column():
    async with engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE icon_ads ADD COLUMN impression_count INTEGER DEFAULT 0'))
            print('Column added successfully')
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(add_column())
