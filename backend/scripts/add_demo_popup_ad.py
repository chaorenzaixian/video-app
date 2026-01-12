"""添加演示弹窗广告"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ad import Advertisement, AdPosition, AdType


async def add_demo_popup_ad():
    async with AsyncSessionLocal() as db:
        # 检查是否已存在弹窗广告
        result = await db.execute(
            select(Advertisement).where(Advertisement.position == AdPosition.HOME_POPUP)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Popup ad exists: ID={existing.id}")
            return
        
        # 创建演示弹窗广告
        ad = Advertisement(
            title="VIP会员限时特惠",
            description="新用户首月仅需9.9元，畅享全站内容",
            media_url="/images/backgrounds/vip_promo.webp",
            target_url="/user/vip",
            position=AdPosition.HOME_POPUP,
            ad_type=AdType.IMAGE,
            priority=100,
            is_active=True
        )
        
        db.add(ad)
        await db.commit()
        print(f"Demo popup ad added: ID={ad.id}")


if __name__ == "__main__":
    asyncio.run(add_demo_popup_ad())
