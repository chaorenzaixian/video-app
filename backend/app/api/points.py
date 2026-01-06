"""
积分与任务系统API
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserVIP
from app.models.points import (
    UserPoints, Task, TaskRecord, PointLog, ExchangeItem, ExchangeRecord
)

router = APIRouter(prefix="/points", tags=["积分任务"])


# ==================== Schemas ====================

class TaskResponse(BaseModel):
    id: int
    task_type: str
    task_name: str
    task_desc: Optional[str]
    points_reward: int
    daily_limit: int
    icon: Optional[str]
    icon_bg: Optional[str]
    action_type: str
    action_url: Optional[str]
    # 用户状态
    today_completed: int = 0
    can_claim: bool = False
    status: str = "todo"  # todo/pending/claimed


class PointsInfoResponse(BaseModel):
    total_points: int
    available_points: int
    frozen_points: int
    invite_count: int


class ExchangeItemResponse(BaseModel):
    id: int
    item_name: str
    item_desc: Optional[str] = None
    item_type: str
    item_value: int
    points_cost: int
    stock: int
    daily_limit: int
    icon: Optional[str] = None
    image_url: Optional[str] = None
    today_exchanged: int = 0


class PointLogResponse(BaseModel):
    id: int
    change_amount: int
    change_type: str
    remark: Optional[str]
    created_at: datetime


# ==================== 辅助函数 ====================

async def get_or_create_user_points(db: AsyncSession, user_id: int) -> UserPoints:
    """获取或创建用户积分记录"""
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == user_id)
    )
    points = result.scalar_one_or_none()
    
    if not points:
        points = UserPoints(user_id=user_id)
        db.add(points)
        await db.commit()
        await db.refresh(points)
    
    return points


async def add_points(
    db: AsyncSession, 
    user_id: int, 
    amount: int, 
    change_type: str,
    source_type: str = None,
    source_id: int = None,
    remark: str = None
):
    """增加积分"""
    user_points = await get_or_create_user_points(db, user_id)
    user_points.available_points += amount
    user_points.total_points += amount
    
    # 记录日志
    log = PointLog(
        user_id=user_id,
        change_amount=amount,
        change_type=change_type,
        source_type=source_type,
        source_id=source_id,
        balance_after=user_points.available_points,
        remark=remark
    )
    db.add(log)
    await db.commit()
    
    return user_points


async def deduct_points(
    db: AsyncSession,
    user_id: int,
    amount: int,
    change_type: str,
    source_type: str = None,
    source_id: int = None,
    remark: str = None
):
    """扣除积分"""
    user_points = await get_or_create_user_points(db, user_id)
    
    if user_points.available_points < amount:
        raise HTTPException(status_code=400, detail="积分不足")
    
    user_points.available_points -= amount
    
    # 记录日志
    log = PointLog(
        user_id=user_id,
        change_amount=-amount,
        change_type=change_type,
        source_type=source_type,
        source_id=source_id,
        balance_after=user_points.available_points,
        remark=remark
    )
    db.add(log)
    await db.commit()
    
    return user_points


# ==================== 积分接口 ====================

@router.get("/info", response_model=PointsInfoResponse)
async def get_points_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户积分信息"""
    user_points = await get_or_create_user_points(db, current_user.id)
    
    # 获取邀请人数
    from app.models.promotion import UserProfile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    invite_count = profile.total_invites if profile else 0
    
    return PointsInfoResponse(
        total_points=user_points.total_points,
        available_points=user_points.available_points,
        frozen_points=user_points.frozen_points,
        invite_count=invite_count
    )


@router.get("/logs", response_model=List[PointLogResponse])
async def get_point_logs(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取积分变动记录"""
    result = await db.execute(
        select(PointLog)
        .where(PointLog.user_id == current_user.id)
        .order_by(PointLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return logs


# ==================== 任务接口 ====================

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表（含完成状态）"""
    # 获取所有激活的任务
    result = await db.execute(
        select(Task).where(Task.is_active == True).order_by(Task.sort_order)
    )
    tasks = result.scalars().all()
    
    # 今日开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    task_responses = []
    for task in tasks:
        # 查询今日完成次数
        count_result = await db.execute(
            select(func.count(TaskRecord.id))
            .where(
                TaskRecord.user_id == current_user.id,
                TaskRecord.task_id == task.id,
                TaskRecord.completed_at >= today_start
            )
        )
        today_completed = count_result.scalar() or 0
        
        # 查询是否有待领取的
        pending_result = await db.execute(
            select(TaskRecord)
            .where(
                TaskRecord.user_id == current_user.id,
                TaskRecord.task_id == task.id,
                TaskRecord.status == "pending"
            )
        )
        has_pending = pending_result.scalar_one_or_none() is not None
        
        # 判断状态
        if has_pending:
            status = "pending"
            can_claim = True
        elif task.daily_limit > 0 and today_completed >= task.daily_limit:
            status = "claimed"
            can_claim = False
        else:
            status = "todo"
            can_claim = False
        
        task_responses.append(TaskResponse(
            id=task.id,
            task_type=task.task_type,
            task_name=task.task_name,
            task_desc=task.task_desc,
            points_reward=task.points_reward,
            daily_limit=task.daily_limit,
            icon=task.icon,
            icon_bg=task.icon_bg,
            action_type=task.action_type,
            action_url=task.action_url,
            today_completed=today_completed,
            can_claim=can_claim,
            status=status
        ))
    
    return task_responses


# ==================== 特定任务接口（必须在参数化路由前面） ====================

@router.post("/tasks/checkin")
async def checkin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """签到（一键完成+领取）"""
    # 获取签到任务（先查询所有，调试用）
    all_result = await db.execute(
        select(Task).where(Task.task_type == "checkin")
    )
    all_task = all_result.scalar_one_or_none()
    
    if all_task:
        print(f"[DEBUG] Found checkin task: id={all_task.id}, is_active={all_task.is_active}")
        if not all_task.is_active:
            # 自动激活任务
            all_task.is_active = True
            await db.commit()
            print(f"[DEBUG] Activated checkin task")
    else:
        print("[DEBUG] No checkin task found in database!")
        raise HTTPException(status_code=404, detail="签到任务未配置，请联系管理员")
    
    task = all_task
    
    # 检查今日是否已签到
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(TaskRecord.id))
        .where(
            TaskRecord.user_id == current_user.id,
            TaskRecord.task_type == "checkin",
            TaskRecord.completed_at >= today_start,
            TaskRecord.status == "claimed"
        )
    )
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="今日已签到")
    
    # 创建记录并直接领取
    record = TaskRecord(
        user_id=current_user.id,
        task_id=task.id,
        task_type="checkin",
        points_earned=task.points_reward,
        status="claimed"
    )
    db.add(record)
    
    # 发放积分
    await add_points(
        db,
        current_user.id,
        task.points_reward,
        change_type="task",
        source_type="checkin",
        remark="每日签到"
    )
    
    return {"message": "签到成功", "points": task.points_reward}


@router.post("/tasks/download")
async def claim_download_reward(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取下载APP奖励"""
    # 获取下载任务（先查询所有，调试用）
    all_result = await db.execute(
        select(Task).where(Task.task_type == "download")
    )
    all_task = all_result.scalar_one_or_none()
    
    if all_task:
        print(f"[DEBUG] Found download task: id={all_task.id}, is_active={all_task.is_active}")
        if not all_task.is_active:
            # 自动激活任务
            all_task.is_active = True
            await db.commit()
            print(f"[DEBUG] Activated download task")
    else:
        print("[DEBUG] No download task found in database!")
        raise HTTPException(status_code=404, detail="下载任务未配置，请联系管理员")
    
    task = all_task
    
    # 检查是否已领取过
    exist_result = await db.execute(
        select(TaskRecord).where(
            TaskRecord.user_id == current_user.id,
            TaskRecord.task_type == "download",
            TaskRecord.status == "claimed"
        )
    )
    if exist_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已领取过下载奖励")
    
    # 创建任务记录
    record = TaskRecord(
        user_id=current_user.id,
        task_id=task.id,
        task_type="download",
        points_earned=task.points_reward,
        status="claimed"
    )
    db.add(record)
    
    # 发放积分
    await add_points(
        db,
        current_user.id,
        task.points_reward,
        change_type="task",
        source_type="download",
        remark="下载APP奖励"
    )
    
    return {"message": "领取成功", "points": task.points_reward}


# ==================== 通用任务接口 ====================

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """完成任务（创建待领取记录）"""
    # 获取任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task or not task.is_active:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查今日完成次数
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(TaskRecord.id))
        .where(
            TaskRecord.user_id == current_user.id,
            TaskRecord.task_id == task_id,
            TaskRecord.completed_at >= today_start
        )
    )
    today_completed = count_result.scalar() or 0
    
    if task.daily_limit > 0 and today_completed >= task.daily_limit:
        raise HTTPException(status_code=400, detail="今日任务已完成")
    
    # 创建完成记录
    record = TaskRecord(
        user_id=current_user.id,
        task_id=task_id,
        task_type=task.task_type,
        points_earned=task.points_reward,
        status="pending"
    )
    db.add(record)
    await db.commit()
    
    return {"message": "任务完成，请领取奖励", "points": task.points_reward}


@router.post("/tasks/{task_id}/claim")
async def claim_task_reward(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取任务奖励"""
    # 查找待领取记录
    result = await db.execute(
        select(TaskRecord)
        .where(
            TaskRecord.user_id == current_user.id,
            TaskRecord.task_id == task_id,
            TaskRecord.status == "pending"
        )
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=400, detail="没有可领取的奖励")
    
    # 发放积分
    await add_points(
        db, 
        current_user.id, 
        record.points_earned,
        change_type="task",
        source_type="task",
        source_id=task_id,
        remark=f"完成任务奖励"
    )
    
    # 更新记录状态
    record.status = "claimed"
    await db.commit()
    
    return {"message": "领取成功", "points": record.points_earned}


# ==================== 兑换接口 ====================

@router.get("/exchange/items", response_model=List[ExchangeItemResponse])
async def get_exchange_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取兑换商品列表"""
    result = await db.execute(
        select(ExchangeItem)
        .where(ExchangeItem.is_active == True)
        .order_by(ExchangeItem.sort_order)
    )
    items = result.scalars().all()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    item_responses = []
    for item in items:
        # 查询今日兑换次数
        count_result = await db.execute(
            select(func.count(ExchangeRecord.id))
            .where(
                ExchangeRecord.user_id == current_user.id,
                ExchangeRecord.item_id == item.id,
                ExchangeRecord.created_at >= today_start
            )
        )
        today_exchanged = count_result.scalar() or 0
        
        item_responses.append(ExchangeItemResponse(
            id=item.id,
            item_name=item.item_name,
            item_desc=item.item_desc,
            item_type=item.item_type,
            item_value=item.item_value,
            points_cost=item.points_cost,
            stock=item.stock,
            daily_limit=item.daily_limit,
            icon=item.icon,
            image_url=item.image_url,
            today_exchanged=today_exchanged
        ))
    
    return item_responses


@router.post("/exchange/{item_id}")
async def exchange_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """兑换商品"""
    # 获取商品
    result = await db.execute(
        select(ExchangeItem).where(ExchangeItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查库存
    if item.stock == 0:
        raise HTTPException(status_code=400, detail="商品已售罄")
    
    # 检查每日限制
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count_result = await db.execute(
        select(func.count(ExchangeRecord.id))
        .where(
            ExchangeRecord.user_id == current_user.id,
            ExchangeRecord.item_id == item_id,
            ExchangeRecord.created_at >= today_start
        )
    )
    today_exchanged = count_result.scalar() or 0
    
    if item.daily_limit > 0 and today_exchanged >= item.daily_limit:
        raise HTTPException(status_code=400, detail="今日兑换次数已达上限")
    
    # 检查积分
    user_points = await get_or_create_user_points(db, current_user.id)
    if user_points.available_points < item.points_cost:
        raise HTTPException(status_code=400, detail="积分不足")
    
    # 扣除积分
    await deduct_points(
        db,
        current_user.id,
        item.points_cost,
        change_type="exchange",
        source_type="exchange",
        source_id=item_id,
        remark=f"兑换{item.item_name}"
    )
    
    # 减少库存
    if item.stock > 0:
        item.stock -= 1
    
    # 创建兑换记录
    record = ExchangeRecord(
        user_id=current_user.id,
        item_id=item_id,
        item_name=item.item_name,
        points_spent=item.points_cost,
        status="success"
    )
    db.add(record)
    
    # 发放奖励
    if item.item_type == "vip_days":
        # 发放VIP天数
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        user_vip = vip_result.scalar_one_or_none()
        
        if user_vip:
            if user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
                user_vip.expire_date += timedelta(days=item.item_value)
            else:
                user_vip.expire_date = datetime.utcnow() + timedelta(days=item.item_value)
            user_vip.is_active = True
            if user_vip.vip_level == 0:
                user_vip.vip_level = 1
        else:
            user_vip = UserVIP(
                user_id=current_user.id,
                vip_level=1,
                is_active=True,
                expire_date=datetime.utcnow() + timedelta(days=item.item_value)
            )
            db.add(user_vip)
    
    await db.commit()
    
    return {"message": f"兑换成功！获得{item.item_name}", "item": item.item_name}


@router.get("/exchange/records")
async def get_exchange_records(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取兑换记录"""
    result = await db.execute(
        select(ExchangeRecord)
        .where(ExchangeRecord.user_id == current_user.id)
        .order_by(ExchangeRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "item_name": r.item_name,
            "points_spent": r.points_spent,
            "status": r.status,
            "created_at": r.created_at
        }
        for r in records
    ]