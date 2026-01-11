"""
添加小说点赞和收藏表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建小说点赞表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS novel_likes (
                    id SERIAL PRIMARY KEY,
                    novel_id INTEGER NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created novel_likes table")
        except Exception as e:
            print(f"novel_likes: {e}")
        
        # 创建唯一索引
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_novel_like_unique 
                ON novel_likes(novel_id, user_id)
            """))
            print("Created idx_novel_like_unique index")
        except Exception as e:
            print(f"idx_novel_like_unique: {e}")
        
        # 创建小说收藏表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS novel_collects (
                    id SERIAL PRIMARY KEY,
                    novel_id INTEGER NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created novel_collects table")
        except Exception as e:
            print(f"novel_collects: {e}")
        
        # 创建唯一索引
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_novel_collect_unique 
                ON novel_collects(novel_id, user_id)
            """))
            print("Created idx_novel_collect_unique index")
        except Exception as e:
            print(f"idx_novel_collect_unique: {e}")
        
        print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())
