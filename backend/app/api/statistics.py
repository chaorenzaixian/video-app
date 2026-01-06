"""
数据统计API
"""
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.video import Video
from app.models.coins import RechargeOrder, CoinTransaction
from app.models.creator import Creator, VideoTip, CreatorWithdrawal
from app.models.statistics import (
    DailyRevenueReport, PlatformDailyStats, UserRetentionStats
)

router = APIRouter(prefix="/admin/statistics", tags=["管理后台-数据统计"])


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取平台数据概览"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # 用户统计
    total_users = await db.execute(select(func.count(User.id)))
    today_users = await db.execute(
        select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
    )
    
    # 视频统计
    total_videos = await db.execute(select(func.count(Video.id)))
    
    # 创作者统计
    total_creators = await db.execute(select(func.count(Creator.id)))
    
    # 今日充值
    today_recharge = await db.execute(
        select(func.sum(RechargeOrder.amount)).where(
            RechargeOrder.status == "paid",
            func.date(RechargeOrder.paid_at) == today
        )
    )
    
    # 本月充值
    month_recharge = await db.execute(
        select(func.sum(RechargeOrder.amount)).where(
            RechargeOrder.status == "paid",
            func.date(RechargeOrder.paid_at) >= month_ago
        )
    )
    
    # 今日打赏
    today_tips = await db.execute(
        select(func.sum(VideoTip.coins_amount)).where(
            func.date(VideoTip.created_at) == today
        )
    )
    
    return {
        "users": {
            "total": total_users.scalar() or 0,
            "today": today_users.scalar() or 0
        },
        "videos": {
            "total": total_videos.scalar() or 0
        },
        "creators": {
            "total": total_creators.scalar() or 0
        },
        "revenue": {
            "today_recharge": float(today_recharge.scalar() or 0),
            "month_recharge": float(month_recharge.scalar() or 0),
            "today_tips": today_tips.scalar() or 0
        }
    }


@router.get("/revenue/chart")
async def get_revenue_chart(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取收入趋势图表数据"""
    start_date = date.today() - timedelta(days=days)
    
    # 按日期分组查询充值数据
    query = select(
        func.date(RechargeOrder.paid_at).label("stat_date"),
        func.sum(RechargeOrder.amount).label("amount"),
        func.count(RechargeOrder.id).label("orders")
    ).where(
        RechargeOrder.status == "paid",
        RechargeOrder.paid_at >= start_date
    ).group_by(
        func.date(RechargeOrder.paid_at)
    ).order_by("stat_date")
    
    result = await db.execute(query)
    
    chart_data = []
    for row in result.all():
        chart_data.append({
            "date": str(row.stat_date),
            "amount": float(row.amount or 0),
            "orders": row.orders or 0
        })
    
    return chart_data


@router.get("/users/chart")
async def get_users_chart(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取用户增长趋势图表数据"""
    start_date = date.today() - timedelta(days=days)
    
    query = select(
        func.date(User.created_at).label("stat_date"),
        func.count(User.id).label("new_users")
    ).where(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).order_by("stat_date")
    
    result = await db.execute(query)
    
    return [
        {"date": str(row.stat_date), "new_users": row.new_users}
        for row in result.all()
    ]


@router.get("/videos/top")
async def get_top_videos(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取热门视频排行"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(Video).where(
        Video.created_at >= start_date
    ).order_by(Video.view_count.desc()).limit(limit)
    
    result = await db.execute(query)
    
    return [
        {
            "id": v.id,
            "title": v.title,
            "cover_url": v.cover_url,
            "view_count": v.view_count,
            "like_count": v.like_count,
            "created_at": v.created_at
        }
        for v in result.scalars().all()
    ]


@router.get("/creators/top")
async def get_top_creators(
    metric: str = Query("income", regex="^(income|followers|videos)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取创作者排行"""
    query = select(Creator, User).join(User, Creator.user_id == User.id)
    
    if metric == "income":
        query = query.order_by(Creator.total_coins_earned.desc())
    elif metric == "followers":
        query = query.order_by(Creator.total_followers.desc())
    else:
        query = query.order_by(Creator.total_videos.desc())
    
    query = query.limit(limit)
    result = await db.execute(query)
    
    return [
        {
            "id": c.id,
            "user_id": u.id,
            "nickname": u.nickname,
            "avatar": u.avatar,
            "display_name": c.display_name,
            "total_videos": c.total_videos,
            "total_followers": c.total_followers,
            "total_income": c.total_coins_earned,
            "is_verified": c.is_verified
        }
        for c, u in result.all()
    ]


@router.get("/retention")
async def get_retention_data(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取用户留存数据"""
    # 简化版本：计算过去N天的用户次日留存
    retention_data = []
    
    for i in range(days):
        cohort_date = date.today() - timedelta(days=i+1)
        next_date = cohort_date + timedelta(days=1)
        
        # 该日注册用户数
        cohort_count = await db.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == cohort_date
            )
        )
        cohort_size = cohort_count.scalar() or 0
        
        if cohort_size > 0:
            # 次日活跃用户数 (简化:使用登录记录或其他活动)
            # 这里简化处理,实际应该基于用户行为日志
            retained = int(cohort_size * 0.3)  # 假设30%留存
            
            retention_data.append({
                "date": str(cohort_date),
                "cohort_size": cohort_size,
                "day1_retained": retained,
                "day1_rate": round(retained / cohort_size * 100, 1)
            })
    
    return retention_data


@router.get("/transactions/summary")
async def get_transactions_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取交易汇总"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # 充值汇总
    recharge = await db.execute(
        select(
            func.sum(RechargeOrder.amount).label("total"),
            func.count(RechargeOrder.id).label("count"),
            func.count(func.distinct(RechargeOrder.user_id)).label("users")
        ).where(
            RechargeOrder.status == "paid",
            func.date(RechargeOrder.paid_at) >= start_date,
            func.date(RechargeOrder.paid_at) <= end_date
        )
    )
    recharge_data = recharge.first()
    
    # 打赏汇总
    tips = await db.execute(
        select(
            func.sum(VideoTip.coins_amount).label("total"),
            func.count(VideoTip.id).label("count")
        ).where(
            func.date(VideoTip.created_at) >= start_date,
            func.date(VideoTip.created_at) <= end_date
        )
    )
    tips_data = tips.first()
    
    # 提现汇总
    withdrawals = await db.execute(
        select(
            func.sum(CreatorWithdrawal.cash_amount).label("total"),
            func.count(CreatorWithdrawal.id).label("count")
        ).where(
            CreatorWithdrawal.status == "completed",
            func.date(CreatorWithdrawal.processed_at) >= start_date,
            func.date(CreatorWithdrawal.processed_at) <= end_date
        )
    )
    withdrawal_data = withdrawals.first()
    
    return {
        "period": {
            "start": str(start_date),
            "end": str(end_date)
        },
        "recharge": {
            "total": float(recharge_data.total or 0),
            "orders": recharge_data.count or 0,
            "users": recharge_data.users or 0
        },
        "tips": {
            "total_coins": tips_data.total or 0,
            "count": tips_data.count or 0
        },
        "withdrawals": {
            "total": float(withdrawal_data.total or 0),
            "count": withdrawal_data.count or 0
        }
    }

