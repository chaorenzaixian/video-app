"""
添加用户最后查看通知时间字段
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        try:
            # 检查字段是否存在
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_notification_read'
            """))
            if result.fetchone():
                print("字段已存在")
                return
            
            # 添加字段
            await conn.execute(text("""
                ALTER TABLE users ADD COLUMN last_notification_read TIMESTAMP
            """))
            print("添加 last_notification_read 字段成功")
        except Exception as e:
            print(f"迁移失败: {e}")
            # 尝试 SQLite 语法
            try:
                await conn.execute(text("""
                    ALTER TABLE users ADD COLUMN last_notification_read DATETIME
                """))
                print("添加 last_notification_read 字段成功 (SQLite)")
            except Exception as e2:
                print(f"SQLite 迁移也失败: {e2}")

if __name__ == "__main__":
    asyncio.run(migrate())
