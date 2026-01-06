"""
后台财务管理API - 金币流水、订单管理
"""
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.coins import UserCoins, CoinTransaction, RechargePackage, RechargeOrder, VideoPurchase, CollectionPurchase

router = APIRouter(prefix="/admin/finance", tags=["后台-财务管理"])


# ==================== 金币流水 ====================

class CoinTransactionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    amount: int
    balance_after: int
    transaction_type: str
    source_type: Optional[str]
    source_id: Optional[int]
    description: Optional[str]
    created_at: datetime


class TransactionListResponse(BaseModel):
    items: List[CoinTransactionResponse]
    total: int
    page: int
    page_size: int
    # 统计数据
    total_recharge: int = 0
    total_spend: int = 0


@router.get("/coin-transactions", response_model=TransactionListResponse)
async def get_coin_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    transaction_type: Optional[str] = None,  # recharge/purchase/tip/earn/refund/admin
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取金币流水列表"""
    query = select(CoinTransaction, User).join(User, CoinTransaction.user_id == User.id)
    count_query = select(func.count(CoinTransaction.id))
    
    # 过滤条件
    if user_id:
        query = query.where(CoinTransaction.user_id == user_id)
        count_query = count_query.where(CoinTransaction.user_id == user_id)
    
    if transaction_type:
        query = query.where(CoinTransaction.transaction_type == transaction_type)
        count_query = count_query.where(CoinTransaction.transaction_type == transaction_type)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.where(CoinTransaction.created_at >= start)
        count_query = count_query.where(CoinTransaction.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.where(CoinTransaction.created_at <= end)
        count_query = count_query.where(CoinTransaction.created_at <= end)
    
    if min_amount:
        query = query.where(func.abs(CoinTransaction.amount) >= min_amount)
        count_query = count_query.where(func.abs(CoinTransaction.amount) >= min_amount)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(desc(CoinTransaction.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    items = []
    for tx, user in result.all():
        items.append(CoinTransactionResponse(
            id=tx.id,
            user_id=tx.user_id,
            username=user.username,
            amount=tx.amount,
            balance_after=tx.balance_after,
            transaction_type=tx.transaction_type,
            source_type=tx.source_type,
            source_id=tx.source_id,
            description=tx.description,
            created_at=tx.created_at
        ))
    
    # 统计充值和消费总额
    recharge_result = await db.execute(
        select(func.sum(CoinTransaction.amount)).where(
            CoinTransaction.amount > 0,
            CoinTransaction.transaction_type == "recharge"
        )
    )
    total_recharge = recharge_result.scalar() or 0
    
    spend_result = await db.execute(
        select(func.sum(func.abs(CoinTransaction.amount))).where(
            CoinTransaction.amount < 0
        )
    )
    total_spend = spend_result.scalar() or 0
    
    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_recharge=total_recharge,
        total_spend=total_spend
    )


@router.get("/coin-transactions/stats")
async def get_transaction_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取金币流水统计"""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # 各类型交易统计
    type_stats = {}
    for tx_type in ["recharge", "purchase", "tip", "earn", "refund", "admin"]:
        # 收入
        income = await db.execute(
            select(func.sum(CoinTransaction.amount)).where(
                CoinTransaction.transaction_type == tx_type,
                CoinTransaction.amount > 0,
                CoinTransaction.created_at >= start_date
            )
        )
        # 支出
        expense = await db.execute(
            select(func.sum(func.abs(CoinTransaction.amount))).where(
                CoinTransaction.transaction_type == tx_type,
                CoinTransaction.amount < 0,
                CoinTransaction.created_at >= start_date
            )
        )
        type_stats[tx_type] = {
            "income": income.scalar() or 0,
            "expense": expense.scalar() or 0
        }
    
    # 今日统计
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_recharge = await db.execute(
        select(func.sum(CoinTransaction.amount)).where(
            CoinTransaction.transaction_type == "recharge",
            CoinTransaction.amount > 0,
            CoinTransaction.created_at >= today
        )
    )
    today_spend = await db.execute(
        select(func.sum(func.abs(CoinTransaction.amount))).where(
            CoinTransaction.amount < 0,
            CoinTransaction.created_at >= today
        )
    )
    
    # 总金币流通量
    total_coins = await db.execute(select(func.sum(UserCoins.balance)))
    
    return {
        "by_type": type_stats,
        "today": {
            "recharge": today_recharge.scalar() or 0,
            "spend": today_spend.scalar() or 0
        },
        "total_circulation": total_coins.scalar() or 0,
        "period_days": days
    }


# ==================== 充值订单管理 ====================

@router.get("/recharge-orders")
async def get_recharge_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,  # pending/success/failed/expired
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取充值订单列表"""
    query = select(RechargeOrder, User, RechargePackage).join(
        User, RechargeOrder.user_id == User.id
    ).join(
        RechargePackage, RechargeOrder.package_id == RechargePackage.id
    )
    count_query = select(func.count(RechargeOrder.id))
    
    if status:
        query = query.where(RechargeOrder.status == status)
        count_query = count_query.where(RechargeOrder.status == status)
    
    if user_id:
        query = query.where(RechargeOrder.user_id == user_id)
        count_query = count_query.where(RechargeOrder.user_id == user_id)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.where(RechargeOrder.created_at >= start)
        count_query = count_query.where(RechargeOrder.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.where(RechargeOrder.created_at <= end)
        count_query = count_query.where(RechargeOrder.created_at <= end)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(RechargeOrder.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    orders = []
    for order, user, package in result.all():
        orders.append({
            "id": order.id,
            "order_no": order.order_no,
            "user_id": user.id,
            "username": user.username,
            "package_name": package.name,
            "coins": order.coins,
            "bonus_coins": order.bonus_coins,
            "amount": float(order.amount),
            "payment_method": order.payment_method,
            "status": order.status,
            "created_at": order.created_at,
            "paid_at": order.paid_at
        })
    
    # 统计成功订单金额
    success_amount = await db.execute(
        select(func.sum(RechargeOrder.amount)).where(RechargeOrder.status == "success")
    )
    
    return {
        "items": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_success_amount": float(success_amount.scalar() or 0)
    }


# ==================== 用户金币管理 ====================

@router.get("/user-coins")
async def get_user_coins_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_balance: Optional[int] = None,
    order_by: str = Query("balance", regex="^(balance|total_recharged|total_spent)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取用户金币列表"""
    query = select(UserCoins, User).join(User, UserCoins.user_id == User.id)
    count_query = select(func.count(UserCoins.id))
    
    if min_balance:
        query = query.where(UserCoins.balance >= min_balance)
        count_query = count_query.where(UserCoins.balance >= min_balance)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 排序
    if order_by == "balance":
        query = query.order_by(desc(UserCoins.balance))
    elif order_by == "total_recharged":
        query = query.order_by(desc(UserCoins.total_recharged))
    else:
        query = query.order_by(desc(UserCoins.total_spent))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    items = []
    for coins, user in result.all():
        items.append({
            "user_id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "balance": coins.balance,
            "total_recharged": coins.total_recharged,
            "total_spent": coins.total_spent,
            "updated_at": coins.updated_at
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


class AdminCoinAdjust(BaseModel):
    user_id: int
    amount: int  # 正数增加，负数减少
    reason: str


@router.post("/adjust-coins")
async def admin_adjust_coins(
    data: AdminCoinAdjust,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """管理员调整用户金币"""
    # 获取或创建用户金币记录
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == data.user_id)
    )
    user_coins = result.scalar_one_or_none()
    
    if not user_coins:
        user_coins = UserCoins(user_id=data.user_id)
        db.add(user_coins)
        await db.flush()
    
    # 检查余额（如果是扣减）
    if data.amount < 0 and user_coins.balance < abs(data.amount):
        raise HTTPException(status_code=400, detail="用户余额不足")
    
    # 调整余额
    user_coins.balance += data.amount
    if data.amount > 0:
        user_coins.total_recharged += data.amount
    else:
        user_coins.total_spent += abs(data.amount)
    
    # 创建交易记录
    transaction = CoinTransaction(
        user_id=data.user_id,
        amount=data.amount,
        balance_after=user_coins.balance,
        transaction_type="admin",
        description=f"管理员调整: {data.reason} (操作人: {admin.username})"
    )
    db.add(transaction)
    
    await db.commit()
    
    return {
        "success": True,
        "new_balance": user_coins.balance,
        "message": f"已{'增加' if data.amount > 0 else '扣除'} {abs(data.amount)} 金币"
    }


# ==================== 视频购买记录 ====================

@router.get("/video-purchases")
async def get_video_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    video_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取视频购买记录"""
    from app.models.video import Video
    
    query = select(VideoPurchase, User, Video).join(
        User, VideoPurchase.user_id == User.id
    ).join(
        Video, VideoPurchase.video_id == Video.id
    )
    count_query = select(func.count(VideoPurchase.id))
    
    if video_id:
        query = query.where(VideoPurchase.video_id == video_id)
        count_query = count_query.where(VideoPurchase.video_id == video_id)
    
    if user_id:
        query = query.where(VideoPurchase.user_id == user_id)
        count_query = count_query.where(VideoPurchase.user_id == user_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(VideoPurchase.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    items = []
    for purchase, user, video in result.all():
        items.append({
            "id": purchase.id,
            "user_id": user.id,
            "username": user.username,
            "video_id": video.id,
            "video_title": video.title,
            "coin_price": purchase.coin_price,
            "created_at": purchase.created_at
        })
    
    # 统计总收入
    total_revenue = await db.execute(
        select(func.sum(VideoPurchase.coin_price))
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_revenue": total_revenue.scalar() or 0
    }












