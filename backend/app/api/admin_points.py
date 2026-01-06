"""
福利任务后台管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.points import Task, ExchangeItem, UserPoints, PointLog

router = APIRouter(prefix="/admin", tags=["后台-福利任务"])


# ==================== Schemas ====================

class TaskCreate(BaseModel):
    task_type: str
    task_name: str
    task_desc: str
    points_reward: int = 5
    daily_limit: int = 1
    icon: str = "🎁"
    icon_bg: str = "linear-gradient(360deg, #9e52cf, #4d45bf)"
    action_type: str = "claim"
    action_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_desc: Optional[str] = None
    points_reward: Optional[int] = None
    daily_limit: Optional[int] = None
    icon: Optional[str] = None
    icon_bg: Optional[str] = None
    action_type: Optional[str] = None
    action_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    task_type: str
    task_name: Optional[str] = None
    task_desc: Optional[str] = None
    points_reward: int = 0
    daily_limit: int = 1
    icon: Optional[str] = None
    icon_bg: Optional[str] = None
    action_type: Optional[str] = "claim"
    action_url: Optional[str] = None
    sort_order: int = 0
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExchangeItemCreate(BaseModel):
    item_name: str
    item_desc: Optional[str] = None
    item_type: str = "vip_card"
    points_cost: int
    item_value: int = 1
    stock: int = -1
    is_active: bool = True
    image_url: Optional[str] = None


class ExchangeItemUpdate(BaseModel):
    item_name: Optional[str] = None
    item_desc: Optional[str] = None
    item_type: Optional[str] = None
    points_cost: Optional[int] = None
    item_value: Optional[int] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None


class ExchangeItemResponse(BaseModel):
    id: int
    item_name: str
    item_desc: Optional[str] = None
    item_type: Optional[str] = "vip_card"
    points_cost: int = 0
    item_value: int = 0
    stock: int = -1
    is_active: Optional[bool] = True
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPointsResponse(BaseModel):
    user_id: int
    username: str
    nickname: Optional[str]
    total_points: int
    available_points: int
    frozen_points: int


class PointLogResponse(BaseModel):
    id: int
    change_type: Optional[str] = None
    change_amount: int = 0
    remark: Optional[str] = None
    balance_after: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PointsAdjust(BaseModel):
    type: str  # add or reduce
    amount: int
    reason: str


# ==================== 任务管理 API ====================

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    result = await db.execute(
        select(Task).order_by(Task.sort_order, Task.id)
    )
    tasks = result.scalars().all()
    return tasks


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    # 检查任务类型是否已存在
    existing = await db.execute(
        select(Task).where(Task.task_type == data.task_type)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该任务类型已存在")
    
    task = Task(**data.dict())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    await db.delete(task)
    await db.commit()
    return {"success": True, "message": "删除成功"}


# ==================== 积分兑换商品管理 API ====================

@router.get("/exchange-items")
async def get_exchange_items(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取兑换商品列表"""
    result = await db.execute(
        select(ExchangeItem).order_by(ExchangeItem.points_cost)
    )
    items = result.scalars().all()
    # 手动转换为字典，确保包含image_url
    return [
        {
            "id": item.id,
            "item_name": item.item_name,
            "item_desc": item.item_desc,
            "item_type": item.item_type,
            "points_cost": item.points_cost,
            "item_value": item.item_value,
            "stock": item.stock,
            "is_active": item.is_active,
            "image_url": item.image_url,
            "created_at": item.created_at
        }
        for item in items
    ]


@router.post("/exchange-items", response_model=ExchangeItemResponse)
async def create_exchange_item(
    data: ExchangeItemCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建兑换商品"""
    item = ExchangeItem(**data.dict())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/exchange-items/{item_id}", response_model=ExchangeItemResponse)
async def update_exchange_item(
    item_id: int,
    data: ExchangeItemUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新兑换商品"""
    result = await db.execute(select(ExchangeItem).where(ExchangeItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/exchange-items/{item_id}")
async def delete_exchange_item(
    item_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除兑换商品"""
    result = await db.execute(select(ExchangeItem).where(ExchangeItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    await db.delete(item)
    await db.commit()
    return {"success": True, "message": "删除成功"}


# ==================== 用户积分查询 API ====================

@router.get("/user-points")
async def get_user_points(
    page: int = 1,
    page_size: int = 20,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户积分列表"""
    # 构建查询
    query = select(
        User.id.label('user_id'),
        User.username,
        User.nickname,
        func.coalesce(UserPoints.total_points, 0).label('total_points'),
        func.coalesce(UserPoints.available_points, 0).label('available_points'),
        func.coalesce(UserPoints.frozen_points, 0).label('frozen_points')
    ).outerjoin(UserPoints, User.id == UserPoints.user_id)
    
    # 过滤条件
    if user_id:
        try:
            query = query.where(User.id == int(user_id))
        except ValueError:
            pass
    if username:
        query = query.where(User.username.ilike(f"%{username}%"))
    
    # 获取总数
    count_query = select(func.count()).select_from(User)
    if user_id:
        try:
            count_query = count_query.where(User.id == int(user_id))
        except ValueError:
            pass
    if username:
        count_query = count_query.where(User.username.ilike(f"%{username}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    items = [dict(row._mapping) for row in result.fetchall()]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/user-points/{user_id}/logs", response_model=List[PointLogResponse])
async def get_user_point_logs(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户积分明细"""
    result = await db.execute(
        select(PointLog)
        .where(PointLog.user_id == user_id)
        .order_by(PointLog.created_at.desc())
        .limit(100)
    )
    logs = result.scalars().all()
    return logs


@router.post("/user-points/{user_id}/adjust")
async def adjust_user_points(
    user_id: int,
    data: PointsAdjust,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """调整用户积分"""
    # 检查用户是否存在
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取或创建用户积分记录
    points_result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == user_id)
    )
    user_points = points_result.scalar_one_or_none()
    
    if not user_points:
        user_points = UserPoints(
            user_id=user_id,
            total_points=0,
            available_points=0,
            frozen_points=0
        )
        db.add(user_points)
        await db.flush()
    
    # 计算积分变动
    if data.type == 'add':
        change_amount = data.amount
        user_points.total_points += data.amount
        user_points.available_points += data.amount
        change_type = 'admin_add'
    else:
        change_amount = -data.amount
        if user_points.available_points < data.amount:
            raise HTTPException(status_code=400, detail="用户可用积分不足")
        user_points.available_points -= data.amount
        change_type = 'admin_reduce'
    
    # 记录积分日志
    log = PointLog(
        user_id=user_id,
        change_type=change_type,
        change_amount=change_amount,
        balance_after=user_points.available_points,
        remark=f"管理员调整: {data.reason}",
        source_type="admin",
        source_id=current_admin.id
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"积分调整成功，当前可用积分: {user_points.available_points}"
    }
