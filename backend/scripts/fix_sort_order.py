"""
重置图标广告排序值为连续数字
"""
import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import select, update
from app.core.database import engine, AsyncSessionLocal
from app.models.ad import IconAd

async def fix_sort():
    async with AsyncSessionLocal() as db:
        # 按当前顺序获取所有广告
        result = await db.execute(
            select(IconAd).order_by(IconAd.sort_order, IconAd.id)
        )
        ads = result.scalars().all()
        
        print("Before fix:")
        for ad in ads:
            print(f"  id={ad.id}, sort={ad.sort_order}, name={ad.name}")
        
        # 重新设置连续的排序值
        print("\nFixing sort_order...")
        for i, ad in enumerate(ads, 1):
            ad.sort_order = i
        
        await db.commit()
        
        # 验证结果
        result = await db.execute(
            select(IconAd).order_by(IconAd.sort_order, IconAd.id)
        )
        ads = result.scalars().all()
        
        print("\nAfter fix:")
        for ad in ads:
            print(f"  id={ad.id}, sort={ad.sort_order}, name={ad.name}")

asyncio.run(fix_sort())
