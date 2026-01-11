"""更新评论表结构，使其与视频评论一致"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def update_tables():
    async with engine.begin() as conn:
        # 更新 gallery_comments 表
        columns = [
            ("image_url", "VARCHAR(500)"),
            ("reply_count", "INTEGER DEFAULT 0"),
            ("is_pinned", "BOOLEAN DEFAULT FALSE"),
            ("is_hidden", "BOOLEAN DEFAULT FALSE"),
            ("is_official", "BOOLEAN DEFAULT FALSE"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]
        
        for col_name, col_type in columns:
            try:
                await conn.execute(text(f"ALTER TABLE gallery_comments ADD COLUMN {col_name} {col_type}"))
                print(f"Added gallery_comments.{col_name}")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print(f"gallery_comments.{col_name} already exists")
                else:
                    print(f"gallery_comments.{col_name}: {e}")
        
        # 更新 post_comments 表（如果需要）
        for col_name, col_type in [("image_url", "VARCHAR(500)"), ("is_official", "BOOLEAN DEFAULT FALSE"), ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")]:
            try:
                await conn.execute(text(f"ALTER TABLE post_comments ADD COLUMN {col_name} {col_type}"))
                print(f"Added post_comments.{col_name}")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print(f"post_comments.{col_name} already exists")
                else:
                    print(f"post_comments.{col_name}: {e}")

if __name__ == "__main__":
    asyncio.run(update_tables())
