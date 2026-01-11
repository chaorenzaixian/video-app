"""
添加帖子收藏表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建帖子收藏表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS post_collects (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created post_collects table")
        except Exception as e:
            print(f"post_collects: {e}")
        
        # 创建唯一索引
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_post_collect_unique 
                ON post_collects(post_id, user_id)
            """))
            print("Created idx_post_collect_unique index")
        except Exception as e:
            print(f"idx_post_collect_unique: {e}")
        
        # 创建user_id索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_post_collect_user 
                ON post_collects(user_id)
            """))
            print("Created idx_post_collect_user index")
        except Exception as e:
            print(f"idx_post_collect_user: {e}")
        
        # 添加collect_count字段到posts表
        try:
            await conn.execute(text("""
                ALTER TABLE posts ADD COLUMN IF NOT EXISTS collect_count INTEGER DEFAULT 0
            """))
            print("Added collect_count column to posts")
        except Exception as e:
            print(f"collect_count column: {e}")
        
        print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())
