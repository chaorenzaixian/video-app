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
from app.core.database import async_session_maker
from app.models.ad import Advertisement, AdPosition


async def fix_popup_ad_image():
    """修复弹窗广告图片"""
    async with async_session_maker() as db:
        # 查找所有弹窗广告
        result = await db.execute(
            select(Advertisement).where(
                Advertisement.position == AdPosition.HOME_POPUP
            )
        )
        ads = result.scalars().all()
        
        if not ads:
            print("没有找到弹窗广告")
            return
        
        for ad in ads:
            print(f"广告 ID: {ad.id}, 标题: {ad.title}")
            print(f"  当前图片: {ad.media_url}")
            
            # 如果图片是不存在的 vip_promo.webp，更新为 vip_recommend.webp
            if ad.media_url and 'vip_promo.webp' in ad.media_url:
                new_url = '/images/backgrounds/vip_recommend.webp'
                ad.media_url = new_url
                print(f"  更新为: {new_url}")
        
        await db.commit()
        print("\n修复完成！")


if __name__ == "__main__":
    asyncio.run(fix_popup_ad_image())
