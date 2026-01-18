"""
交友模块后台管理API
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from pydantic import BaseModel
from PIL import Image
import io

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.dating import DatingGroup, DatingHost

router = APIRouter(prefix="/admin/dating", tags=["交友管理"])

# 上传目录
UPLOAD_DIR = os.path.join(settings.UPLOAD_DIR, "dating")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ========== Schemas ==========
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    join_url: Optional[str] = None
    member_count: str = "0"
    coin_cost: int = 0
    is_free: bool = False
    category: str = "soul"
    sort_order: int = 0


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    join_url: Optional[str] = None
    member_count: Optional[str] = None
    coin_cost: Optional[int] = None
    is_free: Optional[bool] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    join_url: Optional[str] = None
    member_count: str = "0"
    coin_cost: int = 0
    is_free: bool = False
    category: str = "soul"
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class HostCreate(BaseModel):
    nickname: str
    avatar: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    cup: Optional[str] = None
    chat_count: int = 0
    is_vip: bool = False
    is_ace: bool = False
    profile_url: Optional[str] = None
    category: str = "chat"
    sub_category: Optional[str] = None
    sort_order: int = 0


class HostUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    cup: Optional[str] = None
    chat_count: Optional[int] = None
    is_vip: Optional[bool] = None
    is_ace: Optional[bool] = None
    profile_url: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class HostResponse(BaseModel):
    id: int
    nickname: str
    avatar: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    cup: Optional[str] = None
    chat_count: int = 0
    is_vip: bool = False
    is_ace: bool = False
    profile_url: Optional[str] = None
    category: str = "chat"
    sub_category: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== 群聊管理 ==========
@router.get("/groups", response_model=dict)
async def get_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取群聊列表"""
    query = select(DatingGroup)
    
    if category:
        query = query.where(DatingGroup.category == category)
    if keyword:
        query = query.where(DatingGroup.name.contains(keyword))
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # 分页
    query = query.order_by(DatingGroup.sort_order.asc(), DatingGroup.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    groups = result.scalars().all()
    
    # 处理可能为None的字段
    items = []
    for g in groups:
        items.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "avatar": g.avatar,
            "join_url": g.join_url,
            "member_count": g.member_count or "0",
            "coin_cost": g.coin_cost or 0,
            "is_free": g.is_free if g.is_free is not None else False,
            "category": g.category or "soul",
            "sort_order": g.sort_order or 0,
            "is_active": g.is_active if g.is_active is not None else True,
            "created_at": g.created_at
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/groups", response_model=GroupResponse)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建群聊"""
    group = DatingGroup(**data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return GroupResponse.model_validate(group)


@router.put("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新群聊"""
    result = await db.execute(select(DatingGroup).where(DatingGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="群聊不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    
    group.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(group)
    return GroupResponse.model_validate(group)


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除群聊"""
    result = await db.execute(select(DatingGroup).where(DatingGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="群聊不存在")
    
    await db.delete(group)
    await db.commit()
    return {"message": "删除成功"}


@router.delete("/groups/batch")
async def batch_delete_groups(
    ids: List[int],
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """批量删除群聊"""
    await db.execute(delete(DatingGroup).where(DatingGroup.id.in_(ids)))
    await db.commit()
    return {"message": f"成功删除 {len(ids)} 个群聊"}


# ========== 主播管理 ==========
@router.get("/hosts", response_model=dict)
async def get_hosts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sub_category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取主播列表"""
    query = select(DatingHost)
    
    if category:
        query = query.where(DatingHost.category == category)
    if sub_category:
        query = query.where(DatingHost.sub_category == sub_category)
    if keyword:
        query = query.where(DatingHost.nickname.contains(keyword))
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # 分页
    query = query.order_by(DatingHost.sort_order.asc(), DatingHost.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    hosts = result.scalars().all()
    
    # 处理可能为None的字段
    items = []
    for h in hosts:
        items.append({
            "id": h.id,
            "nickname": h.nickname,
            "avatar": h.avatar,
            "age": h.age,
            "height": h.height,
            "weight": h.weight,
            "cup": h.cup,
            "chat_count": h.chat_count or 0,
            "is_vip": h.is_vip if h.is_vip is not None else False,
            "is_ace": h.is_ace if h.is_ace is not None else False,
            "profile_url": h.profile_url,
            "category": h.category or "chat",
            "sub_category": h.sub_category,
            "sort_order": h.sort_order or 0,
            "is_active": h.is_active if h.is_active is not None else True,
            "created_at": h.created_at
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/hosts", response_model=HostResponse)
async def create_host(
    data: HostCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建主播"""
    host = DatingHost(**data.model_dump())
    db.add(host)
    await db.commit()
    await db.refresh(host)
    return HostResponse.model_validate(host)


@router.put("/hosts/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: int,
    data: HostUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新主播"""
    try:
        result = await db.execute(select(DatingHost).where(DatingHost.id == host_id))
        host = result.scalar_one_or_none()
        
        if not host:
            raise HTTPException(status_code=404, detail="主播不存在")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(host, key, value)
        
        host.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(host)
        return HostResponse.model_validate(host)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error updating host {host_id}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/hosts/{host_id}")
async def delete_host(
    host_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除主播"""
    result = await db.execute(select(DatingHost).where(DatingHost.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(status_code=404, detail="主播不存在")
    
    await db.delete(host)
    await db.commit()
    return {"message": "删除成功"}


@router.delete("/hosts/batch")
async def batch_delete_hosts(
    ids: List[int],
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """批量删除主播"""
    await db.execute(delete(DatingHost).where(DatingHost.id.in_(ids)))
    await db.commit()
    return {"message": f"成功删除 {len(ids)} 个主播"}


# ========== 图片上传 ==========
@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user)
):
    """上传图片并转换为webp格式"""
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    try:
        # 读取图片
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        # 转换为RGB（处理RGBA等格式）
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 生成文件名
        filename = f"{uuid.uuid4().hex}.webp"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # 保存为webp格式
        image.save(filepath, 'WEBP', quality=85)
        
        # 返回URL
        url = f"/uploads/dating/{filename}"
        return {"url": url, "filename": filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")
