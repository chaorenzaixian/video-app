"""
添加代理等级配置的迁移脚本
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

async def add_agent_level_configs():
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 代理等级配置项
        configs = [
            # 等级1 - 普通级
            ("agent_level_1_name", "普通级", "代理等级1名称", "agent_levels"),
            ("agent_level_1_rate", "40", "代理等级1返利比例(%)", "agent_levels"),
            ("agent_level_1_condition", "无", "代理等级1条件", "agent_levels"),
            ("agent_level_1_min_users", "0", "代理等级1最低直推人数", "agent_levels"),
            ("agent_level_1_min_sub_agents", "0", "代理等级1最低直属代理数", "agent_levels"),
            ("agent_level_1_min_sub_level", "0", "代理等级1最低直属代理等级", "agent_levels"),
            
            # 等级2 - 青铜级
            ("agent_level_2_name", "青铜级", "代理等级2名称", "agent_levels"),
            ("agent_level_2_rate", "46", "代理等级2返利比例(%)", "agent_levels"),
            ("agent_level_2_condition", "累计直推5个付费会员", "代理等级2条件", "agent_levels"),
            ("agent_level_2_min_users", "5", "代理等级2最低直推人数", "agent_levels"),
            ("agent_level_2_min_sub_agents", "0", "代理等级2最低直属代理数", "agent_levels"),
            ("agent_level_2_min_sub_level", "0", "代理等级2最低直属代理等级", "agent_levels"),
            
            # 等级3 - 白银级
            ("agent_level_3_name", "白银级", "代理等级3名称", "agent_levels"),
            ("agent_level_3_rate", "52", "代理等级3返利比例(%)", "agent_levels"),
            ("agent_level_3_condition", "累计直推20个付费会员+2个直属青铜以上代理", "代理等级3条件", "agent_levels"),
            ("agent_level_3_min_users", "20", "代理等级3最低直推人数", "agent_levels"),
            ("agent_level_3_min_sub_agents", "2", "代理等级3最低直属代理数", "agent_levels"),
            ("agent_level_3_min_sub_level", "2", "代理等级3最低直属代理等级(青铜)", "agent_levels"),
            
            # 等级4 - 黄金级
            ("agent_level_4_name", "黄金级", "代理等级4名称", "agent_levels"),
            ("agent_level_4_rate", "58", "代理等级4返利比例(%)", "agent_levels"),
            ("agent_level_4_condition", "累计直推50个付费会员+2个直属白银以上代理", "代理等级4条件", "agent_levels"),
            ("agent_level_4_min_users", "50", "代理等级4最低直推人数", "agent_levels"),
            ("agent_level_4_min_sub_agents", "2", "代理等级4最低直属代理数", "agent_levels"),
            ("agent_level_4_min_sub_level", "3", "代理等级4最低直属代理等级(白银)", "agent_levels"),
            
            # 等级5 - 铂金级
            ("agent_level_5_name", "铂金级", "代理等级5名称", "agent_levels"),
            ("agent_level_5_rate", "64", "代理等级5返利比例(%)", "agent_levels"),
            ("agent_level_5_condition", "累计直推100个付费会员+2个直属黄金以上代理", "代理等级5条件", "agent_levels"),
            ("agent_level_5_min_users", "100", "代理等级5最低直推人数", "agent_levels"),
            ("agent_level_5_min_sub_agents", "2", "代理等级5最低直属代理数", "agent_levels"),
            ("agent_level_5_min_sub_level", "4", "代理等级5最低直属代理等级(黄金)", "agent_levels"),
            
            # 等级6 - 钻石级
            ("agent_level_6_name", "钻石级", "代理等级6名称", "agent_levels"),
            ("agent_level_6_rate", "70", "代理等级6返利比例(%)", "agent_levels"),
            ("agent_level_6_condition", "累计直推400个付费会员+2个直属铂金以上代理", "代理等级6条件", "agent_levels"),
            ("agent_level_6_min_users", "400", "代理等级6最低直推人数", "agent_levels"),
            ("agent_level_6_min_sub_agents", "2", "代理等级6最低直属代理数", "agent_levels"),
            ("agent_level_6_min_sub_level", "5", "代理等级6最低直属代理等级(铂金)", "agent_levels"),
        ]
        
        for key, value, description, group_name in configs:
            # 检查是否已存在
            result = await session.execute(
                text("SELECT id FROM system_configs WHERE key = :key"),
                {"key": key}
            )
            if result.scalar_one_or_none():
                print(f"[SKIP] Config '{key}' already exists")
                continue
            
            # 插入配置
            await session.execute(
                text("""
                    INSERT INTO system_configs (key, value, description, group_name, created_at, updated_at)
                    VALUES (:key, :value, :description, :group_name, NOW(), NOW())
                """),
                {"key": key, "value": value, "description": description, "group_name": group_name}
            )
            print(f"[OK] Added config '{key}'")
        
        await session.commit()
        print("[DONE] Agent levels configs migration completed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_agent_level_configs())

添加代理等级配置的迁移脚本
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

async def add_agent_level_configs():
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 代理等级配置项
        configs = [
            # 等级1 - 普通级
            ("agent_level_1_name", "普通级", "代理等级1名称", "agent_levels"),
            ("agent_level_1_rate", "40", "代理等级1返利比例(%)", "agent_levels"),
            ("agent_level_1_condition", "无", "代理等级1条件", "agent_levels"),
            ("agent_level_1_min_users", "0", "代理等级1最低直推人数", "agent_levels"),
            ("agent_level_1_min_sub_agents", "0", "代理等级1最低直属代理数", "agent_levels"),
            ("agent_level_1_min_sub_level", "0", "代理等级1最低直属代理等级", "agent_levels"),
            
            # 等级2 - 青铜级
            ("agent_level_2_name", "青铜级", "代理等级2名称", "agent_levels"),
            ("agent_level_2_rate", "46", "代理等级2返利比例(%)", "agent_levels"),
            ("agent_level_2_condition", "累计直推5个付费会员", "代理等级2条件", "agent_levels"),
            ("agent_level_2_min_users", "5", "代理等级2最低直推人数", "agent_levels"),
            ("agent_level_2_min_sub_agents", "0", "代理等级2最低直属代理数", "agent_levels"),
            ("agent_level_2_min_sub_level", "0", "代理等级2最低直属代理等级", "agent_levels"),
            
            # 等级3 - 白银级
            ("agent_level_3_name", "白银级", "代理等级3名称", "agent_levels"),
            ("agent_level_3_rate", "52", "代理等级3返利比例(%)", "agent_levels"),
            ("agent_level_3_condition", "累计直推20个付费会员+2个直属青铜以上代理", "代理等级3条件", "agent_levels"),
            ("agent_level_3_min_users", "20", "代理等级3最低直推人数", "agent_levels"),
            ("agent_level_3_min_sub_agents", "2", "代理等级3最低直属代理数", "agent_levels"),
            ("agent_level_3_min_sub_level", "2", "代理等级3最低直属代理等级(青铜)", "agent_levels"),
            
            # 等级4 - 黄金级
            ("agent_level_4_name", "黄金级", "代理等级4名称", "agent_levels"),
            ("agent_level_4_rate", "58", "代理等级4返利比例(%)", "agent_levels"),
            ("agent_level_4_condition", "累计直推50个付费会员+2个直属白银以上代理", "代理等级4条件", "agent_levels"),
            ("agent_level_4_min_users", "50", "代理等级4最低直推人数", "agent_levels"),
            ("agent_level_4_min_sub_agents", "2", "代理等级4最低直属代理数", "agent_levels"),
            ("agent_level_4_min_sub_level", "3", "代理等级4最低直属代理等级(白银)", "agent_levels"),
            
            # 等级5 - 铂金级
            ("agent_level_5_name", "铂金级", "代理等级5名称", "agent_levels"),
            ("agent_level_5_rate", "64", "代理等级5返利比例(%)", "agent_levels"),
            ("agent_level_5_condition", "累计直推100个付费会员+2个直属黄金以上代理", "代理等级5条件", "agent_levels"),
            ("agent_level_5_min_users", "100", "代理等级5最低直推人数", "agent_levels"),
            ("agent_level_5_min_sub_agents", "2", "代理等级5最低直属代理数", "agent_levels"),
            ("agent_level_5_min_sub_level", "4", "代理等级5最低直属代理等级(黄金)", "agent_levels"),
            
            # 等级6 - 钻石级
            ("agent_level_6_name", "钻石级", "代理等级6名称", "agent_levels"),
            ("agent_level_6_rate", "70", "代理等级6返利比例(%)", "agent_levels"),
            ("agent_level_6_condition", "累计直推400个付费会员+2个直属铂金以上代理", "代理等级6条件", "agent_levels"),
            ("agent_level_6_min_users", "400", "代理等级6最低直推人数", "agent_levels"),
            ("agent_level_6_min_sub_agents", "2", "代理等级6最低直属代理数", "agent_levels"),
            ("agent_level_6_min_sub_level", "5", "代理等级6最低直属代理等级(铂金)", "agent_levels"),
        ]
        
        for key, value, description, group_name in configs:
            # 检查是否已存在
            result = await session.execute(
                text("SELECT id FROM system_configs WHERE key = :key"),
                {"key": key}
            )
            if result.scalar_one_or_none():
                print(f"[SKIP] Config '{key}' already exists")
                continue
            
            # 插入配置
            await session.execute(
                text("""
                    INSERT INTO system_configs (key, value, description, group_name, created_at, updated_at)
                    VALUES (:key, :value, :description, :group_name, NOW(), NOW())
                """),
                {"key": key, "value": value, "description": description, "group_name": group_name}
            )
            print(f"[OK] Added config '{key}'")
        
        await session.commit()
        print("[DONE] Agent levels configs migration completed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_agent_level_configs())

