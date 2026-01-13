"""
为轮播图添加统计字段
"""
import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

async def add_stats_columns():
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    
    async with engine.begin() as conn:
        # 添加 impression_count
        if is_sqlite:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('banners') WHERE name='impression_count'"
            ))
        else:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='banners' AND column_name='impression_count'"
            ))
        
        if not result.scalar():
            await conn.execute(text("ALTER TABLE banners ADD COLUMN impression_count INTEGER DEFAULT 0"))
            print("[OK] Added impression_count to banners")
        else:
            print("[INFO] impression_count already exists")
        
        # 添加 click_count
        if is_sqlite:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('banners') WHERE name='click_count'"
            ))
        else:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='banners' AND column_name='click_count'"
            ))
        
        if not result.scalar():
            await conn.execute(text("ALTER TABLE banners ADD COLUMN click_count INTEGER DEFAULT 0"))
            print("[OK] Added click_count to banners")
        else:
            print("[INFO] click_count already exists")

if __name__ == "__main__":
    asyncio.run(add_stats_columns())
