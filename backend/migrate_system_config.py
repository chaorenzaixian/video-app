"""
数据库迁移脚本 - 添加系统配置表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.models.system_config import DEFAULT_CONFIGS

async def migrate():
    async with engine.begin() as conn:
        # 1. 创建 system_configs 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_configs (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value TEXT,
                    description VARCHAR(255),
                    group_name VARCHAR(50) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created system_configs table")
        except Exception as e:
            print(f"[SKIP] system_configs table: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_system_configs_key 
                ON system_configs(key)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_system_configs_group 
                ON system_configs(group_name)
            """))
            print("[OK] Created indexes")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        # 3. 插入默认配置
        for config in DEFAULT_CONFIGS:
            try:
                await conn.execute(text("""
                    INSERT INTO system_configs (key, value, description, group_name)
                    VALUES (:key, :value, :description, :group_name)
                    ON CONFLICT (key) DO NOTHING
                """), config)
            except Exception as e:
                print(f"[SKIP] Config {config['key']}: {e}")
        
        print("[OK] Inserted default configs")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

数据库迁移脚本 - 添加系统配置表
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine
from app.models.system_config import DEFAULT_CONFIGS

async def migrate():
    async with engine.begin() as conn:
        # 1. 创建 system_configs 表
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS system_configs (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value TEXT,
                    description VARCHAR(255),
                    group_name VARCHAR(50) DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created system_configs table")
        except Exception as e:
            print(f"[SKIP] system_configs table: {e}")
        
        # 2. 创建索引
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_system_configs_key 
                ON system_configs(key)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_system_configs_group 
                ON system_configs(group_name)
            """))
            print("[OK] Created indexes")
        except Exception as e:
            print(f"[SKIP] Indexes: {e}")
        
        # 3. 插入默认配置
        for config in DEFAULT_CONFIGS:
            try:
                await conn.execute(text("""
                    INSERT INTO system_configs (key, value, description, group_name)
                    VALUES (:key, :value, :description, :group_name)
                    ON CONFLICT (key) DO NOTHING
                """), config)
            except Exception as e:
                print(f"[SKIP] Config {config['key']}: {e}")
        
        print("[OK] Inserted default configs")
        
        await conn.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

