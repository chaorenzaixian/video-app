"""
修复弹窗广告图片路径
将不存在的 vip_promo.webp 改为存在的 vip_recommend.webp
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.ad import Advertisement, AdPosition


async def fix_popup_ad_image():
    """修复弹窗广告图片"""
    async with AsyncSessionLocal() as db:
        # 查找所有弹窗广告
        result = await db.execute(
            select(Advertisement).where(
                Advertisement.position == AdPosition.HOME_POPUP
            )
        )
        ads = result.scalars().all()
        
        if not ads:
            print("No popup ads found")
            return
        
        updated = 0
        for ad in ads:
            print(f"Ad ID: {ad.id}, Title: {ad.title}")
            print(f"  Current image: {ad.media_url}")
            
            # 如果图片是不存在的 vip_promo.webp，更新为 vip_recommend.webp
            if ad.media_url and 'vip_promo.webp' in ad.media_url:
                new_url = '/images/backgrounds/vip_recommend.webp'
                ad.media_url = new_url
                print(f"  Updated to: {new_url}")
                updated += 1
        
        await db.commit()
        print(f"\nDone! Updated {updated} ads.")


if __name__ == "__main__":
    asyncio.run(fix_popup_ad_image())
