"""
积分任务系统数据库迁移脚本
"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        # 创建用户积分表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_points (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                total_points INTEGER DEFAULT 0,
                available_points INTEGER DEFAULT 0,
                frozen_points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created user_points table")

        # 创建任务配置表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(50) NOT NULL UNIQUE,
                task_name VARCHAR(100) NOT NULL,
                task_desc VARCHAR(255),
                points_reward INTEGER DEFAULT 0,
                daily_limit INTEGER DEFAULT 1,
                icon VARCHAR(255),
                icon_bg VARCHAR(50),
                action_type VARCHAR(50) DEFAULT 'claim',
                action_url VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created tasks table")

        # 创建任务记录表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS task_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                task_id INTEGER NOT NULL REFERENCES tasks(id),
                task_type VARCHAR(50),
                completed_at TIMESTAMP DEFAULT NOW(),
                points_earned INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending'
            )
        """))
        print("[OK] Created task_records table")

        # 创建积分日志表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS point_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                change_amount INTEGER NOT NULL,
                change_type VARCHAR(50),
                source_type VARCHAR(50),
                source_id INTEGER,
                balance_after INTEGER,
                remark VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created point_logs table")

        # 创建兑换商品表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_items (
                id SERIAL PRIMARY KEY,
                item_name VARCHAR(100) NOT NULL,
                item_type VARCHAR(50),
                item_value INTEGER,
                points_cost INTEGER NOT NULL,
                stock INTEGER DEFAULT -1,
                daily_limit INTEGER DEFAULT 1,
                icon VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created exchange_items table")

        # 创建兑换记录表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                item_id INTEGER NOT NULL REFERENCES exchange_items(id),
                item_name VARCHAR(100),
                points_spent INTEGER,
                status VARCHAR(20) DEFAULT 'success',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created exchange_records table")

        # 插入默认任务
        await session.execute(text("""
            INSERT INTO tasks (task_type, task_name, task_desc, points_reward, daily_limit, icon, icon_bg, action_type, sort_order)
            VALUES 
                ('checkin', '每日签到', '每天签到获取积分', 10, 1, '📅', '#8b5cf6', 'claim', 1),
                ('watch_video', '观看视频', '观看任意视频1分钟', 5, 5, '🎬', '#ec4899', 'redirect', 2),
                ('share', '分享视频', '分享视频给好友', 10, 3, '🔗', '#f97316', 'redirect', 3),
                ('comment', '发表评论', '对视频发表评论', 5, 5, '💬', '#22c55e', 'redirect', 4),
                ('invite', '邀请好友', '邀请好友注册', 50, 0, '👥', '#3b82f6', 'redirect', 5)
            ON CONFLICT (task_type) DO NOTHING
        """))
        print("[OK] Inserted default tasks")

        # 插入默认兑换商品
        await session.execute(text("""
            INSERT INTO exchange_items (item_name, item_type, item_value, points_cost, stock, daily_limit, icon, sort_order)
            VALUES 
                ('VIP会员1天', 'vip_days', 1, 100, -1, 1, '/images/icons/vip_1d.webp', 1),
                ('VIP会员3天', 'vip_days', 3, 250, -1, 1, '/images/icons/vip_3d.webp', 2),
                ('VIP会员7天', 'vip_days', 7, 500, -1, 1, '/images/icons/vip_7d.webp', 3),
                ('VIP会员30天', 'vip_days', 30, 1800, -1, 1, '/images/icons/vip_30d.webp', 4)
            ON CONFLICT DO NOTHING
        """))
        print("[OK] Inserted default exchange items")

        await session.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())


"""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        # 创建用户积分表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_points (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                total_points INTEGER DEFAULT 0,
                available_points INTEGER DEFAULT 0,
                frozen_points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created user_points table")

        # 创建任务配置表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(50) NOT NULL UNIQUE,
                task_name VARCHAR(100) NOT NULL,
                task_desc VARCHAR(255),
                points_reward INTEGER DEFAULT 0,
                daily_limit INTEGER DEFAULT 1,
                icon VARCHAR(255),
                icon_bg VARCHAR(50),
                action_type VARCHAR(50) DEFAULT 'claim',
                action_url VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created tasks table")

        # 创建任务记录表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS task_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                task_id INTEGER NOT NULL REFERENCES tasks(id),
                task_type VARCHAR(50),
                completed_at TIMESTAMP DEFAULT NOW(),
                points_earned INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending'
            )
        """))
        print("[OK] Created task_records table")

        # 创建积分日志表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS point_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                change_amount INTEGER NOT NULL,
                change_type VARCHAR(50),
                source_type VARCHAR(50),
                source_id INTEGER,
                balance_after INTEGER,
                remark VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created point_logs table")

        # 创建兑换商品表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_items (
                id SERIAL PRIMARY KEY,
                item_name VARCHAR(100) NOT NULL,
                item_type VARCHAR(50),
                item_value INTEGER,
                points_cost INTEGER NOT NULL,
                stock INTEGER DEFAULT -1,
                daily_limit INTEGER DEFAULT 1,
                icon VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created exchange_items table")

        # 创建兑换记录表
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                item_id INTEGER NOT NULL REFERENCES exchange_items(id),
                item_name VARCHAR(100),
                points_spent INTEGER,
                status VARCHAR(20) DEFAULT 'success',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("[OK] Created exchange_records table")

        # 插入默认任务
        await session.execute(text("""
            INSERT INTO tasks (task_type, task_name, task_desc, points_reward, daily_limit, icon, icon_bg, action_type, sort_order)
            VALUES 
                ('checkin', '每日签到', '每天签到获取积分', 10, 1, '📅', '#8b5cf6', 'claim', 1),
                ('watch_video', '观看视频', '观看任意视频1分钟', 5, 5, '🎬', '#ec4899', 'redirect', 2),
                ('share', '分享视频', '分享视频给好友', 10, 3, '🔗', '#f97316', 'redirect', 3),
                ('comment', '发表评论', '对视频发表评论', 5, 5, '💬', '#22c55e', 'redirect', 4),
                ('invite', '邀请好友', '邀请好友注册', 50, 0, '👥', '#3b82f6', 'redirect', 5)
            ON CONFLICT (task_type) DO NOTHING
        """))
        print("[OK] Inserted default tasks")

        # 插入默认兑换商品
        await session.execute(text("""
            INSERT INTO exchange_items (item_name, item_type, item_value, points_cost, stock, daily_limit, icon, sort_order)
            VALUES 
                ('VIP会员1天', 'vip_days', 1, 100, -1, 1, '/images/icons/vip_1d.webp', 1),
                ('VIP会员3天', 'vip_days', 3, 250, -1, 1, '/images/icons/vip_3d.webp', 2),
                ('VIP会员7天', 'vip_days', 7, 500, -1, 1, '/images/icons/vip_7d.webp', 3),
                ('VIP会员30天', 'vip_days', 30, 1800, -1, 1, '/images/icons/vip_30d.webp', 4)
            ON CONFLICT DO NOTHING
        """))
        print("[OK] Inserted default exchange items")

        await session.commit()
        print("\n[DONE] Migration completed!")

if __name__ == "__main__":
    asyncio.run(migrate())

