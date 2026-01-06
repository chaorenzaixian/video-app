"""
添加提现配置项的迁移脚本
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

async def add_withdraw_configs():
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 提现配置项
        configs = [
            ("withdraw_fee_rate", "20", "提现手续费率(%)", "withdraw"),
            ("withdraw_min_amount", "250", "最低提现金额(元)", "withdraw"),
            ("withdraw_max_amount", "10000", "单笔最高提现金额(元)", "withdraw"),
            ("withdraw_rule_1", "每次提现金额最低250元起，单笔提现最大10000元，且为整数。", "提现规则1", "withdraw"),
            ("withdraw_rule_2", "每次提现收取20%手续费。", "提现规则2", "withdraw"),
            ("withdraw_rule_3", "支持银行卡或USDT提现，收款账户卡号与姓名一致，到账时间不超72小时内", "提现规则3", "withdraw"),
            ("withdraw_rule_4", "申请提现后请随时关注收款账户进款通知，长时间未到账，请及时联系客服", "提现规则4", "withdraw"),
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
        print("[DONE] Withdraw configs migration completed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_withdraw_configs())


"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings

async def add_withdraw_configs():
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 提现配置项
        configs = [
            ("withdraw_fee_rate", "20", "提现手续费率(%)", "withdraw"),
            ("withdraw_min_amount", "250", "最低提现金额(元)", "withdraw"),
            ("withdraw_max_amount", "10000", "单笔最高提现金额(元)", "withdraw"),
            ("withdraw_rule_1", "每次提现金额最低250元起，单笔提现最大10000元，且为整数。", "提现规则1", "withdraw"),
            ("withdraw_rule_2", "每次提现收取20%手续费。", "提现规则2", "withdraw"),
            ("withdraw_rule_3", "支持银行卡或USDT提现，收款账户卡号与姓名一致，到账时间不超72小时内", "提现规则3", "withdraw"),
            ("withdraw_rule_4", "申请提现后请随时关注收款账户进款通知，长时间未到账，请及时联系客服", "提现规则4", "withdraw"),
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
        print("[DONE] Withdraw configs migration completed!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_withdraw_configs())

