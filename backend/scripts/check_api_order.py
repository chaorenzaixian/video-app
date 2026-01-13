import asyncio
import sys
sys.path.insert(0, '/www/wwwroot/video-app/backend')

from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal
from app.models.ad import IconAd

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IconAd)
            .where(IconAd.is_active == True)
            .order_by(IconAd.sort_order, IconAd.id)
        )
        ads = result.scalars().all()
        
        print("Database order (sort_order, id):")
        for ad in ads:
            print(f"  sort={ad.sort_order}, id={ad.id}, name={ad.name}")

asyncio.run(check())
