"""
为现有用户分配默认头像
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User


def generate_default_avatar(user_id: int) -> str:
    """根据用户ID生成默认头像路径"""
    total_avatars = 52
    index = user_id % total_avatars
    
    if index < 17:
        return f"/images/avatars/icon_avatar_{index + 1}.webp"
    elif index < 32:
        num = str(index - 17 + 1).zfill(3)
        return f"/images/avatars/DM_20251217202131_{num}.JPEG"
    else:
        num = str(index - 32 + 1).zfill(3)
        webp_files = ['002', '006', '015', '018']
        ext = 'webp' if num in webp_files else 'JPEG'
        return f"/images/avatars/DM_20251217202341_{num}.{ext}"


async def migrate_avatars():
    async with AsyncSessionLocal() as db:
        # 查找没有头像的用户
        result = await db.execute(
            select(User).where(
                (User.avatar == None) | (User.avatar == '')
            )
        )
        users = result.scalars().all()
        
        print(f"找到 {len(users)} 个没有头像的用户")
        
        updated = 0
        for user in users:
            user.avatar = generate_default_avatar(user.id)
            updated += 1
            if updated % 100 == 0:
                print(f"已处理 {updated} 个用户...")
        
        await db.commit()
        print(f"✓ 完成！共更新 {updated} 个用户的头像")


if __name__ == "__main__":
    asyncio.run(migrate_avatars())
