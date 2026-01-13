"""Revert popup ad to original state"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ad import Advertisement, AdPosition

async def revert():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Advertisement).where(Advertisement.position == AdPosition.HOME_POPUP)
        )
        ad = result.scalar_one_or_none()
        if ad:
            ad.media_url = '/images/backgrounds/vip_promo.webp'
            await db.commit()
            print(f'Reverted popup ad #{ad.id} to /images/backgrounds/vip_promo.webp')
        else:
            print('No popup ad found')

if __name__ == "__main__":
    asyncio.run(revert())
