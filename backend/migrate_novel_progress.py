"""
添加小说阅读进度表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建阅读进度表 (PostgreSQL语法)
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS novel_read_progress (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    novel_id INTEGER NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    chapter_id INTEGER REFERENCES novel_chapters(id) ON DELETE SET NULL,
                    chapter_num INTEGER DEFAULT 1,
                    scroll_position REAL DEFAULT 0,
                    audio_position REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created novel_read_progress table")
        except Exception as e:
            print(f"novel_read_progress: {e}")
        
        # 创建唯一索引
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_novel_progress_unique 
                ON novel_read_progress(user_id, novel_id)
            """))
            print("✓ Created idx_novel_progress_unique index")
        except Exception as e:
            print(f"idx_novel_progress_unique: {e}")
        
        print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())
