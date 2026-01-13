"""Fix popup ad image path and create demo popup ad if not exists"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.ad import Advertisement, AdPosition, AdType

async def fix():
    async with AsyncSessionLocal() as db:
        # 检查是否已有弹窗广告
        result = await db.execute(
            select(Advertisement).where(Advertisement.position == AdPosition.HOME_POPUP)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新现有广告的图片路径
            existing.media_url = '/images/backgrounds/vip_recommend.webp'
            await db.commit()
            print(f'Updated popup ad #{existing.id} image to /images/backgrounds/vip_recommend.webp')
        else:
            # 创建新的弹窗广告
            ad = Advertisement(
                title='VIP会员推荐',
                description='开通VIP，畅享无限精彩内容',
                ad_type=AdType.IMAGE,
                media_url='/images/backgrounds/vip_recommend.webp',
                target_url='/user/vip',
                position=AdPosition.HOME_POPUP,
                priority=10,
                duration=0,
                is_active=True
            )
            db.add(ad)
            await db.commit()
            print('Created new popup ad with /images/backgrounds/vip_recommend.webp')

if __name__ == "__main__":
    asyncio.run(fix())
