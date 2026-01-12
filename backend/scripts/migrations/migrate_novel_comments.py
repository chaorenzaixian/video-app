"""
创建小说评论表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建小说评论表 (PostgreSQL 语法)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS novel_comments (
                id SERIAL PRIMARY KEY,
                novel_id INTEGER NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                image_url VARCHAR(500),
                parent_id INTEGER REFERENCES novel_comments(id) ON DELETE CASCADE,
                like_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                is_pinned BOOLEAN DEFAULT FALSE,
                is_hidden BOOLEAN DEFAULT FALSE,
                is_official BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_novel_comments_novel_id ON novel_comments(novel_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_novel_comments_user_id ON novel_comments(user_id)
        """))
        
        # 创建小说评论点赞表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS novel_comment_likes (
                id SERIAL PRIMARY KEY,
                comment_id INTEGER NOT NULL REFERENCES novel_comments(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建唯一索引
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_novel_comment_like_unique 
            ON novel_comment_likes(comment_id, user_id)
        """))
        
        # 确保 novels 表有 comment_count 字段
        try:
            await conn.execute(text("""
                ALTER TABLE novels ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0
            """))
            print("Added comment_count column to novels table")
        except Exception as e:
            print(f"Note: {e}")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
