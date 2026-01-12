"""
添加评论表新字段 (使用asyncpg)
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/video_app")

async def add_columns():
    # 转换URL格式
    db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # 添加 image_url 列
        try:
            await conn.execute("ALTER TABLE comments ADD COLUMN image_url VARCHAR(500)")
            print("Added image_url column")
        except Exception as e:
            print(f"image_url: {e}")
        
        # 添加 is_official 列
        try:
            await conn.execute("ALTER TABLE comments ADD COLUMN is_official BOOLEAN DEFAULT FALSE")
            print("Added is_official column")
        except Exception as e:
            print(f"is_official: {e}")
        
        await conn.close()
        print("Done!")
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(add_columns())
