"""
后台操作日志API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.admin_log import AdminLog
from app.api.deps import get_admin_user

router = APIRouter(prefix="/admin/logs", tags=["后台-操作日志"])


@router.get("/stats")
async def get_admin_log_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取管理员操作日志统计"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    # 今日操作数
    result = await db.execute(
        select(func.count(AdminLog.id)).where(AdminLog.created_at >= today_start)
    )
    today = result.scalar() or 0
    
    # 本周操作数
    result = await db.execute(
        select(func.count(AdminLog.id)).where(AdminLog.created_at >= week_start)
    )
    week = result.scalar() or 0
    
    # 本月操作数
    result = await db.execute(
        select(func.count(AdminLog.id)).where(AdminLog.created_at >= month_start)
    )
    month = result.scalar() or 0
    
    # 总操作数
    result = await db.execute(
        select(func.count(AdminLog.id))
    )
    total = result.scalar() or 0
    
    return {
        "today": today,
        "week": week,
        "month": month,
        "total": total
    }


@router.get("")
async def get_admin_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_id: Optional[int] = None,
    action_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取管理员操作日志"""
    query = select(AdminLog)
    count_query = select(func.count(AdminLog.id))
    
    if admin_id:
        query = query.where(AdminLog.admin_id == admin_id)
        count_query = count_query.where(AdminLog.admin_id == admin_id)
    
    if action_type:
        query = query.where(AdminLog.action_type == action_type)
        count_query = count_query.where(AdminLog.action_type == action_type)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.where(AdminLog.created_at >= start)
        count_query = count_query.where(AdminLog.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.where(AdminLog.created_at <= end)
        count_query = count_query.where(AdminLog.created_at <= end)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(AdminLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "action_type": log.action_type,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "description": log.description,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }







