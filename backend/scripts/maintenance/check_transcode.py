import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.begin() as conn:
        # 查看最近的视频
        result = await conn.execute(text("""
            SELECT id, title, status, original_url, hls_url, preview_url, duration, created_at
            FROM videos 
            ORDER BY id DESC
            LIMIT 10
        """))
        rows = result.fetchall()
        print(f'最近的视频:')
        for r in rows:
            print(f'  ID:{r[0]} 标题:{r[1]} 状态:{r[2]} 时长:{r[6]}')
            print(f'    原始:{r[3]}')
            print(f'    HLS:{r[4]}')
            print(f'    预览:{r[5]}')
            print()

asyncio.run(check())
