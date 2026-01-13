"""
后台内容管理API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.content import Banner, Notice
from app.api.deps import get_admin_user

router = APIRouter(prefix="/admin/content", tags=["后台-内容管理"])


# ==================== 轮播图管理 ====================

class BannerCreate(BaseModel):
    title: str
    image_url: str
    link_url: Optional[str] = None
    link_type: str = "none"  # url/video/vip/none
    link_value: Optional[str] = None  # 链接值
    position: str = "home"
    sort_order: int = 0
    is_active: bool = True
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class BannerUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    link_type: Optional[str] = None
    link_value: Optional[str] = None
    position: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@router.get("/banners")
async def get_banners(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    position: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取轮播图列表"""
    query = select(Banner)
    count_query = select(func.count(Banner.id))
    
    if position:
        query = query.where(Banner.position == position)
        count_query = count_query.where(Banner.position == position)
    
    if is_active is not None:
        query = query.where(Banner.is_active == is_active)
        count_query = count_query.where(Banner.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(Banner.sort_order.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    banners = result.scalars().all()
    
    return {
        "items": [
            {
                "id": b.id,
                "title": b.title,
                "image_url": b.image_url,
                "link_url": b.link_url,
                "link_type": b.link_type or "none",
                "link_value": b.link_url,  # 前端使用 link_value
                "position": b.position,
                "sort_order": b.sort_order,
                "is_active": b.is_active,
                "impression_count": b.impression_count or 0,
                "click_count": b.click_count or 0,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "created_at": b.created_at
            }
            for b in banners
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/banners")
async def create_banner(
    data: BannerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """创建轮播图"""
    banner_data = data.dict(exclude={'link_value'})
    # 如果前端发送了 link_value，用它替代 link_url
    if data.link_value:
        banner_data['link_url'] = data.link_value
    banner = Banner(**banner_data)
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return {"id": banner.id, "message": "创建成功"}


@router.put("/banners/{banner_id}")
async def update_banner(
    banner_id: int,
    data: BannerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """更新轮播图"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    
    update_data = data.dict(exclude_unset=True, exclude={'link_value'})
    # 如果前端发送了 link_value，用它替代 link_url
    if data.link_value is not None:
        update_data['link_url'] = data.link_value
    for key, value in update_data.items():
        setattr(banner, key, value)
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/banners/{banner_id}")
async def delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """删除轮播图"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    
    await db.delete(banner)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/banners/{banner_id}/click")
async def record_banner_click(
    banner_id: int,
    db: AsyncSession = Depends(get_db)
):
    """记录轮播图点击（无需登录）"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(status_code=404, detail="轮播图不存在")
    
    banner.click_count = (banner.click_count or 0) + 1
    await db.commit()
    return {"success": True, "link_url": banner.link_url}


# ==================== 公告管理 ====================

class NoticeCreate(BaseModel):
    title: str
    content: str
    notice_type: str = "system"
    is_popup: bool = False
    is_active: bool = True


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
    is_popup: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/notices")
async def get_notices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    notice_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取公告列表"""
    query = select(Notice)
    count_query = select(func.count(Notice.id))
    
    if notice_type:
        query = query.where(Notice.notice_type == notice_type)
        count_query = count_query.where(Notice.notice_type == notice_type)
    
    if is_active is not None:
        query = query.where(Notice.is_active == is_active)
        count_query = count_query.where(Notice.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(Notice.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    notices = result.scalars().all()
    
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "notice_type": n.notice_type,
                "is_popup": n.is_popup,
                "is_active": n.is_active,
                "created_at": n.created_at
            }
            for n in notices
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/notices")
async def create_notice(
    data: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """创建公告"""
    notice = Notice(**data.dict())
    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return {"id": notice.id, "message": "创建成功"}


@router.put("/notices/{notice_id}")
async def update_notice(
    notice_id: int,
    data: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """更新公告"""
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(notice, key, value)
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/notices/{notice_id}")
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """删除公告"""
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = result.scalar_one_or_none()
    
    if not notice:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    await db.delete(notice)
    await db.commit()
    return {"message": "删除成功"}







