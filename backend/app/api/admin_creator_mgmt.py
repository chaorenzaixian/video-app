"""
后台-创作者管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.creator import Creator, CreatorApplication

router = APIRouter(prefix="/admin/creators-mgmt")


@router.get("/list")
async def get_creators_list(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取创作者列表"""
    query = select(Creator)
    
    if search:
        query = query.join(User).where(User.username.contains(search))
    
    if status:
        query = query.where(Creator.status == status)
    
    # 获取总数
    count_query = select(func.count()).select_from(Creator)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    creators = result.scalars().all()
    
    return {
        "items": creators,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/stats")
async def get_creator_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取创作者统计数据"""
    # 总创作者数
    total_result = await db.execute(select(func.count()).select_from(Creator))
    total = total_result.scalar()
    
    # 活跃创作者数
    active_result = await db.execute(
        select(func.count()).select_from(Creator).where(Creator.status == "active")
    )
    active = active_result.scalar()
    
    # 待审核申请数
    pending_result = await db.execute(
        select(func.count()).select_from(CreatorApplication).where(CreatorApplication.status == "pending")
    )
    pending = pending_result.scalar()
    
    return {
        "total": total or 0,
        "active": active or 0,
        "pending_applications": pending or 0
    }





