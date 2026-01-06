"""
数据库迁移脚本 - 添加二维码登录相关表和字段
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 1. 给 users 表添加 current_session_id 和 current_device_info 字段
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS current_session_id VARCHAR(64),
                ADD COLUMN IF NOT EXISTS current_device_info VARCHAR(500)
            """))
            print("[OK] Added current_session_id and current_device_info to users table")
        except Exception as e:
            print(f"[SKIP] users table columns: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_current_session_id 
                ON users(current_session_id)
            """))
            print("[OK] Created index on current_session_id")
        except Exception as e:
            print(f"[SKIP] Index: {e}")
        
        # 3. 创建 login_qr_tokens 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS login_qr_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP,
                    used_device_info VARCHAR(500),
                    used_ip VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created login_qr_tokens table")
        except Exception as e:
            print(f"[SKIP] login_qr_tokens table: {e}")
        
        # 4. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_login_qr_tokens_token 
                ON login_qr_tokens(token)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_login_qr_tokens_user_id 
                ON login_qr_tokens(user_id)
            """))
            print("[OK] Created indexes on login_qr_tokens")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())


"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 1. 给 users 表添加 current_session_id 和 current_device_info 字段
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS current_session_id VARCHAR(64),
                ADD COLUMN IF NOT EXISTS current_device_info VARCHAR(500)
            """))
            print("[OK] Added current_session_id and current_device_info to users table")
        except Exception as e:
            print(f"[SKIP] users table columns: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_current_session_id 
                ON users(current_session_id)
            """))
            print("[OK] Created index on current_session_id")
        except Exception as e:
            print(f"[SKIP] Index: {e}")
        
        # 3. 创建 login_qr_tokens 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS login_qr_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP,
                    used_device_info VARCHAR(500),
                    used_ip VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created login_qr_tokens table")
        except Exception as e:
            print(f"[SKIP] login_qr_tokens table: {e}")
        
        # 4. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_login_qr_tokens_token 
                ON login_qr_tokens(token)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_login_qr_tokens_user_id 
                ON login_qr_tokens(user_id)
            """))
            print("[OK] Created indexes on login_qr_tokens")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

