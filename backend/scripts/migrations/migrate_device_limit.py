"""
数据库迁移脚本 - 添加设备管理相关表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 1. 创建 trusted_devices 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trusted_devices (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    device_id VARCHAR(64) NOT NULL,
                    device_name VARCHAR(100),
                    device_info VARCHAR(500),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_login_at TIMESTAMP,
                    last_login_ip VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created trusted_devices table")
        except Exception as e:
            print(f"[SKIP] trusted_devices table: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_trusted_devices_user_id 
                ON trusted_devices(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_trusted_devices_device_id 
                ON trusted_devices(device_id)
            """))
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_trusted_devices_user_device 
                ON trusted_devices(user_id, device_id)
            """))
            print("[OK] Created indexes on trusted_devices")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        # 3. 创建 device_switch_logs 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_switch_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    from_device_id VARCHAR(64),
                    to_device_id VARCHAR(64) NOT NULL,
                    to_device_name VARCHAR(100),
                    to_device_ip VARCHAR(50),
                    switched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created device_switch_logs table")
        except Exception as e:
            print(f"[SKIP] device_switch_logs table: {e}")
        
        # 4. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_device_switch_logs_user_id 
                ON device_switch_logs(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_device_switch_logs_switched_at 
                ON device_switch_logs(switched_at)
            """))
            print("[OK] Created indexes on device_switch_logs")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

数据库迁移脚本 - 添加设备管理相关表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 1. 创建 trusted_devices 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trusted_devices (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    device_id VARCHAR(64) NOT NULL,
                    device_name VARCHAR(100),
                    device_info VARCHAR(500),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_login_at TIMESTAMP,
                    last_login_ip VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created trusted_devices table")
        except Exception as e:
            print(f"[SKIP] trusted_devices table: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_trusted_devices_user_id 
                ON trusted_devices(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_trusted_devices_device_id 
                ON trusted_devices(device_id)
            """))
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS ix_trusted_devices_user_device 
                ON trusted_devices(user_id, device_id)
            """))
            print("[OK] Created indexes on trusted_devices")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        # 3. 创建 device_switch_logs 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_switch_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    from_device_id VARCHAR(64),
                    to_device_id VARCHAR(64) NOT NULL,
                    to_device_name VARCHAR(100),
                    to_device_ip VARCHAR(50),
                    switched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created device_switch_logs table")
        except Exception as e:
            print(f"[SKIP] device_switch_logs table: {e}")
        
        # 4. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_device_switch_logs_user_id 
                ON device_switch_logs(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_device_switch_logs_switched_at 
                ON device_switch_logs(switched_at)
            """))
            print("[OK] Created indexes on device_switch_logs")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

