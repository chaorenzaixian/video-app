"""
交友模块用户端API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.dating import DatingGroup, DatingHost

router = APIRouter(prefix="/dating", tags=["交友"])


# ========== Schemas ==========
class GroupItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    join_url: Optional[str] = None
    member_count: str = "0"
    coin_cost: int = 0
    is_free: bool = False
    
    class Config:
        from_attributes = True


class HostItem(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    cup: Optional[str] = None
    chat_count: int = 0
    is_vip: Optional[bool] = False
    is_ace: Optional[bool] = False
    profile_url: Optional[str] = None
    sub_category: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== 群聊列表 ==========
@router.get("/groups", response_model=List[GroupItem])
async def get_groups(
    category: str = Query("soul", description="分类: soul, chat, live"),
    db: AsyncSession = Depends(get_db)
):
    """获取群聊列表"""
    query = select(DatingGroup).where(
        DatingGroup.is_active == True,
        DatingGroup.category == category
    ).order_by(DatingGroup.sort_order.asc(), DatingGroup.id.desc())
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return [GroupItem.model_validate(g) for g in groups]


# ========== 主播列表 ==========
@router.get("/hosts", response_model=List[HostItem])
async def get_hosts(
    category: str = Query("chat", description="分类: chat, live"),
    sub_category: Optional[str] = Query(None, description="子分类"),
    db: AsyncSession = Depends(get_db)
):
    """获取主播列表"""
    query = select(DatingHost).where(
        DatingHost.is_active == True,
        DatingHost.category == category
    )
    
    if sub_category:
        query = query.where(DatingHost.sub_category == sub_category)
    
    query = query.order_by(DatingHost.sort_order.asc(), DatingHost.id.desc())
    
    result = await db.execute(query)
    hosts = result.scalars().all()
    
    return [HostItem.model_validate(h) for h in hosts]
