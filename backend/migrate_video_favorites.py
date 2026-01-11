"""
确保视频收藏表存在并优化索引
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建视频收藏表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS video_favorites (
                    id SERIAL PRIMARY KEY,
                    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created video_favorites table")
        except Exception as e:
            print(f"video_favorites: {e}")
        
        # 创建唯一索引
        try:
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_video_favorite_unique 
                ON video_favorites(video_id, user_id)
            """))
            print("Created idx_video_favorite_unique index")
        except Exception as e:
            print(f"idx_video_favorite_unique: {e}")
        
        # 创建user_id索引加速查询
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_favorite_user 
                ON video_favorites(user_id)
            """))
            print("Created idx_video_favorite_user index")
        except Exception as e:
            print(f"idx_video_favorite_user: {e}")
        
        # 创建video_id索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_favorite_video 
                ON video_favorites(video_id)
            """))
            print("Created idx_video_favorite_video index")
        except Exception as e:
            print(f"idx_video_favorite_video: {e}")
        
        # video_likes表索引优化
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_like_user 
                ON video_likes(user_id)
            """))
            print("Created idx_video_like_user index")
        except Exception as e:
            print(f"idx_video_like_user: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_video_like_video 
                ON video_likes(video_id)
            """))
            print("Created idx_video_like_video index")
        except Exception as e:
            print(f"idx_video_like_video: {e}")
        
        # 确保videos表有favorite_count字段
        try:
            await conn.execute(text("""
                ALTER TABLE videos ADD COLUMN IF NOT EXISTS favorite_count INTEGER DEFAULT 0
            """))
            print("Added favorite_count column to videos")
        except Exception as e:
            print(f"favorite_count column: {e}")
        
        print("Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())
