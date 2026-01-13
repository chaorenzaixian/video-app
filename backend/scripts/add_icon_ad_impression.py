"""
添加图标广告展示统计字段
"""
import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

async def add_impression_count():
    """添加 impression_count 字段到 icon_ads 表"""
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    
    async with engine.begin() as conn:
        if is_sqlite:
            # SQLite 检查字段
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM pragma_table_info('icon_ads') 
                WHERE name='impression_count'
            """))
            exists = result.scalar()
        else:
            # PostgreSQL 检查字段
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name='icon_ads' AND column_name='impression_count'
            """))
            exists = result.scalar()
        
        if not exists:
            await conn.execute(text("""
                ALTER TABLE icon_ads ADD COLUMN impression_count INTEGER DEFAULT 0
            """))
            print("✅ 已添加 impression_count 字段")
        else:
            print("ℹ️ impression_count 字段已存在")

if __name__ == "__main__":
    asyncio.run(add_impression_count())
