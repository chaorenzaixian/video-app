import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id, nickname, sub_category FROM dating_hosts WHERE sub_category = '学生萝莉' ORDER BY sort_order"))
        rows = result.fetchall()
        print(f'学生萝莉分类共有 {len(rows)} 个主播:')
        for r in rows:
            print(f'  {r[0]}: {r[1]}')

asyncio.run(check())
