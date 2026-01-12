"""
交友模块数据库迁移脚本
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 创建群聊表 (PostgreSQL)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dating_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                avatar VARCHAR(500),
                join_url VARCHAR(500),
                member_count VARCHAR(20) DEFAULT '0',
                coin_cost INTEGER DEFAULT 0,
                is_free BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                category VARCHAR(20) DEFAULT 'soul',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建主播表 (PostgreSQL)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dating_hosts (
                id SERIAL PRIMARY KEY,
                nickname VARCHAR(50) NOT NULL,
                avatar VARCHAR(500),
                age INTEGER,
                height INTEGER,
                weight INTEGER,
                cup VARCHAR(5),
                chat_count INTEGER DEFAULT 0,
                is_vip BOOLEAN DEFAULT FALSE,
                is_ace BOOLEAN DEFAULT FALSE,
                profile_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                category VARCHAR(20) DEFAULT 'chat',
                sub_category VARCHAR(30),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 创建索引
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dating_group_status ON dating_groups(is_active, sort_order)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dating_host_status ON dating_hosts(is_active, sort_order)"))
        except:
            pass
        
        print("交友模块表创建成功!")
        
        # 插入示例数据
        await conn.execute(text("""
            INSERT INTO dating_groups (name, description, avatar, member_count, coin_cost, is_free, category)
            VALUES 
            ('大学生约炮聊骚群', '在校大学生排解寂寞，鸡把大的优...', '/images/backgrounds/dating_group_card.webp', '10w', 1000, TRUE, 'soul'),
            ('上海线下绿帽群', '这里可以满足你所有的绿帽癖，绿...', '/images/backgrounds/dating_group_card.webp', '10w', 1000, FALSE, 'soul'),
            ('广州车友约会群', '车友聚集地，开启你不一样的快乐...', '/images/backgrounds/dating_group_card.webp', '10w', 1000, FALSE, 'soul'),
            ('深圳夫妻圈', '真实夫妻换妻，有资源的来互换了...', '/images/backgrounds/dating_group_card.webp', '9w', 900, FALSE, 'soul')
            ON CONFLICT DO NOTHING
        """))
        
        await conn.execute(text("""
            INSERT INTO dating_hosts (nickname, avatar, age, height, weight, cup, chat_count, is_vip, is_ace, category, sub_category)
            VALUES 
            ('奈可萝莉', '/images/backgrounds/dating_user_card.webp', 18, 162, 47, 'C', 1, TRUE, FALSE, 'chat', '学生萝莉'),
            ('小柠檬', '/images/backgrounds/dating_user_card.webp', 18, 168, 48, 'D', 5, TRUE, FALSE, 'chat', '学生萝莉'),
            ('Uu_puppy', '/images/backgrounds/dating_user_card.webp', 20, 165, 50, 'C', 9, FALSE, TRUE, 'live', '主播御姐'),
            ('Yuyouwei-', '/images/backgrounds/dating_user_card.webp', 22, 170, 52, 'D', 2, FALSE, TRUE, 'live', '主播御姐'),
            ('Sakura_Anne', '/images/backgrounds/dating_user_card.webp', 21, 166, 49, 'C', 3, FALSE, TRUE, 'live', '模特兼职'),
            ('camellia-66', '/images/backgrounds/dating_user_card.webp', 23, 168, 51, 'D', 7, FALSE, TRUE, 'live', '人妻少妇')
            ON CONFLICT DO NOTHING
        """))
        
        print("示例数据插入成功!")

if __name__ == "__main__":
    asyncio.run(migrate())
