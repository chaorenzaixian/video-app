import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT id, name, sort_order FROM icon_ads ORDER BY sort_order LIMIT 15'))
        for row in result:
            print(f'id={row[0]}, name={row[1]}, sort={row[2]}')

asyncio.run(check())
