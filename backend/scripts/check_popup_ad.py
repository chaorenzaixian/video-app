"""Check popup ad details"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ad import Advertisement, AdPosition

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Advertisement).where(Advertisement.position == AdPosition.HOME_POPUP)
        )
        ad = result.scalar_one_or_none()
        if ad:
            print('ID:', ad.id)
            print('Title:', ad.title)
            print('media_url:', ad.media_url)
            print('extra_images:', ad.extra_images)
            print('target_url:', ad.target_url)
        else:
            print('No popup ad found')

if __name__ == "__main__":
    asyncio.run(check())
