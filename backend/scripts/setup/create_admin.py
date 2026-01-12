"""
创建管理员账号脚本
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash, generate_invite_code

async def create_admin():
    async with AsyncSessionLocal() as db:
        # 检查管理员是否存在
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.username == 'admin'))
        existing = result.scalar_one_or_none()
        if existing:
            print('Admin already exists')
            return
        
        # 创建管理员
        admin = User(
            username='admin',
            email='admin@example.com',
            hashed_password=get_password_hash('admin123'),
            nickname='Admin',
            role=UserRole.SUPER_ADMIN,
            invite_code=generate_invite_code(),
            is_active=True,
            is_guest=False
        )
        db.add(admin)
        await db.commit()
        print('Admin created successfully!')
        print('Username: admin')
        print('Password: admin123')

if __name__ == '__main__':
    asyncio.run(create_admin())






