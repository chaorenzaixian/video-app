"""添加图集相关字段和表"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def add_columns():
    async with engine.begin() as conn:
        # 添加字段
        try:
            await conn.execute(text("ALTER TABLE galleries ADD COLUMN comment_count INTEGER DEFAULT 0"))
            print("Added comment_count")
        except Exception as e:
            print(f"comment_count: {e}")
        
        try:
            await conn.execute(text("ALTER TABLE galleries ADD COLUMN collect_count INTEGER DEFAULT 0"))
            print("Added collect_count")
        except Exception as e:
            print(f"collect_count: {e}")
        
        # 创建表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gallery_comments (
                    id SERIAL PRIMARY KEY,
                    gallery_id INTEGER NOT NULL REFERENCES galleries(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    parent_id INTEGER REFERENCES gallery_comments(id) ON DELETE CASCADE,
                    like_count INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'visible',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created gallery_comments")
        except Exception as e:
            print(f"gallery_comments: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gallery_likes (
                    id SERIAL PRIMARY KEY,
                    gallery_id INTEGER NOT NULL REFERENCES galleries(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(gallery_id, user_id)
                )
            """))
            print("Created gallery_likes")
        except Exception as e:
            print(f"gallery_likes: {e}")
        
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gallery_collects (
                    id SERIAL PRIMARY KEY,
                    gallery_id INTEGER NOT NULL REFERENCES galleries(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(gallery_id, user_id)
                )
            """))
            print("Created gallery_collects")
        except Exception as e:
            print(f"gallery_collects: {e}")

if __name__ == "__main__":
    asyncio.run(add_columns())
