"""
后台金币管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, delete
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.coins import RechargePackage, RechargeOrder, UserCoins, CoinTransaction

router = APIRouter(prefix="/admin", tags=["后台-金币管理"])


# ============ Schemas ============

class RechargePackageCreate(BaseModel):
    name: str
    coins: int
    bonus_coins: int = 0
    price: float
    original_price: Optional[float] = None
    tag: Optional[str] = None
    sort_order: int = 0
    is_hot: bool = False
    is_first_charge: bool = False
    is_active: bool = True


class RechargePackageUpdate(BaseModel):
    name: Optional[str] = None
    coins: Optional[int] = None
    bonus_coins: Optional[int] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    tag: Optional[str] = None
    sort_order: Optional[int] = None
    is_hot: Optional[bool] = None
    is_first_charge: Optional[bool] = None
    is_active: Optional[bool] = None


class RechargePackageResponse(BaseModel):
    id: int
    name: str
    coins: int
    bonus_coins: int
    price: float
    original_price: Optional[float]
    tag: Optional[str]
    sort_order: int
    is_hot: bool
    is_first_charge: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserCoinsAdjust(BaseModel):
    type: str  # add / reduce
    amount: int
    reason: str


class UserCoinsResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    nickname: Optional[str] = None
    balance: int
    total_recharged: int
    total_spent: int
    total_earned: int


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int


# ============ 充值套餐管理 ============

@router.get("/recharge-packages", response_model=List[RechargePackageResponse])
async def get_recharge_packages(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取所有充值套餐"""
    result = await db.execute(
        select(RechargePackage).order_by(RechargePackage.sort_order)
    )
    packages = result.scalars().all()
    return packages


@router.post("/recharge-packages", response_model=RechargePackageResponse)
async def create_recharge_package(
    data: RechargePackageCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建充值套餐"""
    package = RechargePackage(**data.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


@router.put("/recharge-packages/{package_id}", response_model=RechargePackageResponse)
async def update_recharge_package(
    package_id: int,
    data: RechargePackageUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新充值套餐"""
    result = await db.execute(
        select(RechargePackage).where(RechargePackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(package, key, value)
    
    await db.commit()
    await db.refresh(package)
    return package


@router.delete("/recharge-packages/{package_id}")
async def delete_recharge_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除充值套餐"""
    result = await db.execute(
        select(RechargePackage).where(RechargePackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    await db.delete(package)
    await db.commit()
    return {"message": "删除成功"}


# ============ 充值订单管理 ============

@router.get("/recharge-orders")
async def get_recharge_orders(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取充值订单列表"""
    query = select(RechargeOrder).join(User, RechargeOrder.user_id == User.id)
    
    if status:
        query = query.where(RechargeOrder.status == status)
    
    if keyword:
        query = query.where(
            (User.username.ilike(f"%{keyword}%")) |
            (User.nickname.ilike(f"%{keyword}%")) |
            (RechargeOrder.order_no.ilike(f"%{keyword}%"))
        )
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.order_by(RechargeOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # 构建响应
    items = []
    for order in orders:
        user_result = await db.execute(select(User).where(User.id == order.user_id))
        user = user_result.scalar_one_or_none()
        items.append({
            "id": order.id,
            "order_no": order.order_no,
            "user": {
                "id": user.id if user else None,
                "username": user.username if user else None,
                "nickname": user.nickname if user else None
            } if user else None,
            "coins": order.coins,
            "bonus_coins": order.bonus_coins,
            "amount": float(order.amount),
            "payment_method": order.payment_method,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ============ 用户金币管理 ============

@router.get("/user-coins")
async def get_user_coins(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取用户金币列表"""
    query = select(UserCoins).join(User, UserCoins.user_id == User.id)
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.nickname.ilike(f"%{search}%"))
        )
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.order_by(UserCoins.balance.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    coins_list = result.scalars().all()
    
    items = []
    for uc in coins_list:
        user_result = await db.execute(select(User).where(User.id == uc.user_id))
        user = user_result.scalar_one_or_none()
        items.append({
            "user_id": uc.user_id,
            "username": user.username if user else None,
            "nickname": user.nickname if user else None,
            "balance": uc.balance,
            "total_recharged": uc.total_recharged,
            "total_spent": uc.total_spent,
            "total_earned": uc.total_earned
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/user-coins/{user_id}/adjust")
async def adjust_user_coins(
    user_id: int,
    data: UserCoinsAdjust,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """调整用户金币"""
    # 获取用户金币记录
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == user_id)
    )
    user_coins = result.scalar_one_or_none()
    
    if not user_coins:
        # 创建新记录
        user_coins = UserCoins(user_id=user_id, balance=0)
        db.add(user_coins)
    
    # 计算调整金额
    if data.type == "add":
        amount = data.amount
    else:
        amount = -data.amount
        if user_coins.balance + amount < 0:
            raise HTTPException(status_code=400, detail="金币余额不足")
    
    # 更新余额
    old_balance = user_coins.balance
    user_coins.balance += amount
    
    # 记录交易
    transaction = CoinTransaction(
        user_id=user_id,
        transaction_type="admin",
        amount=amount,
        balance_after=user_coins.balance,
        source_type="system",
        source_id=admin.id,
        description=f"管理员调整: {data.reason}"
    )
    db.add(transaction)
    
    await db.commit()
    
    return {
        "message": "调整成功",
        "old_balance": old_balance,
        "new_balance": user_coins.balance
    }

