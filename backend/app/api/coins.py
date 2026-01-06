"""
金币系统API接口
"""
from datetime import datetime
import uuid
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.coins import (
    UserCoins, CoinTransaction, RechargePackage, RechargeOrder, VideoPurchase
)

router = APIRouter(prefix="/coins", tags=["金币系统"])


# ==================== Schemas ====================

class CoinBalanceResponse(BaseModel):
    balance: int
    total_recharged: int
    total_spent: int
    total_earned: int
    frozen: int

    class Config:
        from_attributes = True


class RechargePackageResponse(BaseModel):
    id: int
    name: str
    coins: int
    bonus_coins: int
    price: float
    original_price: Optional[float] = None
    icon: Optional[str] = None
    tag: Optional[str] = None
    description: Optional[str] = None
    is_hot: bool = False
    is_first_charge: bool = False

    class Config:
        from_attributes = True


class CoinTransactionResponse(BaseModel):
    id: int
    amount: int
    balance_after: int
    transaction_type: str
    source_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateRechargeOrderRequest(BaseModel):
    package_id: int
    payment_method: str  # alipay/wechat


class RechargeOrderResponse(BaseModel):
    order_no: str
    coins: int
    bonus_coins: int
    amount: float
    payment_method: str
    status: str
    pay_url: Optional[str] = None  # 支付链接
    qr_code: Optional[str] = None  # 支付二维码

    class Config:
        from_attributes = True


# ==================== Helper Functions ====================

async def get_or_create_user_coins(db: AsyncSession, user_id: int) -> UserCoins:
    """获取或创建用户金币账户"""
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == user_id)
    )
    user_coins = result.scalar_one_or_none()
    
    if not user_coins:
        user_coins = UserCoins(user_id=user_id)
        db.add(user_coins)
        await db.commit()
        await db.refresh(user_coins)
    
    return user_coins


async def add_coins(
    db: AsyncSession,
    user_id: int,
    amount: int,
    transaction_type: str,
    source_type: str = None,
    source_id: int = None,
    description: str = None,
    extra_data: dict = None
) -> CoinTransaction:
    """添加金币"""
    user_coins = await get_or_create_user_coins(db, user_id)
    user_coins.balance += amount
    
    if transaction_type == "recharge":
        user_coins.total_recharged += amount
    elif transaction_type == "earn":
        user_coins.total_earned += amount
    
    transaction = CoinTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=user_coins.balance,
        transaction_type=transaction_type,
        source_type=source_type,
        source_id=source_id,
        description=description,
        extra_data=extra_data
    )
    db.add(transaction)
    
    return transaction


async def deduct_coins(
    db: AsyncSession,
    user_id: int,
    amount: int,
    transaction_type: str,
    source_type: str = None,
    source_id: int = None,
    description: str = None,
    extra_data: dict = None
) -> CoinTransaction:
    """
    扣除金币（使用行级锁确保并发安全）
    使用 FOR UPDATE 锁定用户金币记录，防止并发扣款导致余额异常
    """
    # 使用 FOR UPDATE 锁定记录，确保并发安全
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == user_id).with_for_update()
    )
    user_coins = result.scalar_one_or_none()
    
    if not user_coins:
        # 如果不存在则创建，使用锁定方式
        user_coins = UserCoins(user_id=user_id)
        db.add(user_coins)
        await db.flush()
        # 重新获取并锁定
        result = await db.execute(
            select(UserCoins).where(UserCoins.user_id == user_id).with_for_update()
        )
        user_coins = result.scalar_one()
    
    if user_coins.balance < amount:
        raise HTTPException(status_code=400, detail="金币余额不足")
    
    user_coins.balance -= amount
    user_coins.total_spent += amount
    
    transaction = CoinTransaction(
        user_id=user_id,
        amount=-amount,
        balance_after=user_coins.balance,
        transaction_type=transaction_type,
        source_type=source_type,
        source_id=source_id,
        description=description,
        extra_data=extra_data
    )
    db.add(transaction)
    
    return transaction


def generate_order_no() -> str:
    """生成订单号"""
    return f"RC{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


# ==================== API Endpoints ====================

@router.get("/balance", response_model=CoinBalanceResponse)
async def get_coin_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取金币余额"""
    user_coins = await get_or_create_user_coins(db, current_user.id)
    return user_coins


@router.get("/packages", response_model=List[RechargePackageResponse])
async def get_recharge_packages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取充值套餐列表"""
    # 检查用户是否有过充值记录
    has_recharged = await db.execute(
        select(func.count(RechargeOrder.id)).where(
            RechargeOrder.user_id == current_user.id,
            RechargeOrder.status == "paid"
        )
    )
    is_first_charge = has_recharged.scalar() == 0
    
    # 获取套餐
    query = select(RechargePackage).where(RechargePackage.is_active == True)
    
    # 如果不是首充，排除首充专享套餐
    if not is_first_charge:
        query = query.where(RechargePackage.is_first_charge == False)
    
    query = query.order_by(RechargePackage.sort_order)
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return [
        RechargePackageResponse(
            id=p.id,
            name=p.name,
            coins=p.coins,
            bonus_coins=p.bonus_coins,
            price=float(p.price),
            original_price=float(p.original_price) if p.original_price else None,
            icon=p.icon,
            tag=p.tag,
            description=p.description,
            is_hot=p.is_hot,
            is_first_charge=p.is_first_charge
        )
        for p in packages
    ]


@router.post("/recharge", response_model=RechargeOrderResponse)
async def create_recharge_order(
    request: Request,
    data: CreateRechargeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建充值订单"""
    # 获取套餐
    result = await db.execute(
        select(RechargePackage).where(
            RechargePackage.id == data.package_id,
            RechargePackage.is_active == True
        )
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    # 检查首充专享
    if package.is_first_charge:
        has_recharged = await db.execute(
            select(func.count(RechargeOrder.id)).where(
                RechargeOrder.user_id == current_user.id,
                RechargeOrder.status == "paid"
            )
        )
        if has_recharged.scalar() > 0:
            raise HTTPException(status_code=400, detail="首充专享套餐仅限首次充值")
    
    # 创建订单
    order = RechargeOrder(
        order_no=generate_order_no(),
        user_id=current_user.id,
        package_id=package.id,
        coins=package.coins,
        bonus_coins=package.bonus_coins,
        amount=package.price,
        payment_method=data.payment_method,
        inviter_id=current_user.inviter_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # TODO: 调用支付接口生成支付链接
    # 这里返回模拟数据，实际需要对接支付平台
    pay_url = f"/api/v1/coins/pay/{order.order_no}"
    
    return RechargeOrderResponse(
        order_no=order.order_no,
        coins=order.coins,
        bonus_coins=order.bonus_coins,
        amount=float(order.amount),
        payment_method=order.payment_method,
        status=order.status,
        pay_url=pay_url
    )


@router.post("/pay/{order_no}/simulate")
async def simulate_payment(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """模拟支付成功(开发测试用)"""
    result = await db.execute(
        select(RechargeOrder).where(
            RechargeOrder.order_no == order_no,
            RechargeOrder.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单状态异常")
    
    # 更新订单状态
    order.status = "paid"
    order.paid_at = datetime.utcnow()
    order.payment_no = f"SIM{uuid.uuid4().hex[:16].upper()}"
    
    # 添加金币
    total_coins = order.coins + order.bonus_coins
    await add_coins(
        db,
        current_user.id,
        total_coins,
        transaction_type="recharge",
        source_type="recharge",
        source_id=order.id,
        description=f"充值{order.coins}金币" + (f"+赠送{order.bonus_coins}" if order.bonus_coins else "")
    )
    
    await db.commit()
    
    return {
        "message": f"充值成功！获得{total_coins}金币",
        "coins": order.coins,
        "bonus_coins": order.bonus_coins,
        "total": total_coins
    }


@router.get("/transactions", response_model=List[CoinTransactionResponse])
async def get_coin_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取金币交易记录"""
    query = select(CoinTransaction).where(CoinTransaction.user_id == current_user.id)
    
    if transaction_type:
        query = query.where(CoinTransaction.transaction_type == transaction_type)
    
    query = query.order_by(CoinTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions


@router.get("/orders")
async def get_recharge_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取充值订单列表"""
    query = select(RechargeOrder).where(RechargeOrder.user_id == current_user.id)
    
    if status:
        query = query.where(RechargeOrder.status == status)
    
    query = query.order_by(RechargeOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        {
            "order_no": o.order_no,
            "coins": o.coins,
            "bonus_coins": o.bonus_coins,
            "amount": float(o.amount),
            "payment_method": o.payment_method,
            "status": o.status,
            "paid_at": o.paid_at,
            "created_at": o.created_at
        }
        for o in orders
    ]


# ==================== 视频购买相关 ====================

@router.post("/purchase/video/{video_id}")
async def purchase_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """购买视频"""
    from app.models.video import Video
    from app.models.user import UserVIP
    
    # 获取视频
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已购买
    existing = await db.execute(
        select(VideoPurchase).where(
            VideoPurchase.user_id == current_user.id,
            VideoPurchase.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已购买过此视频")
    
    # 检查付费类型
    pay_type = getattr(video, 'pay_type', 'free') or 'free'
    coin_price = getattr(video, 'coin_price', 0) or 0
    
    if pay_type == 'free' or coin_price <= 0:
        raise HTTPException(status_code=400, detail="此视频无需购买")
    
    # 获取用户VIP信息
    vip_result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id)
    )
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    # 黄金至尊(5)和钻石至尊(6)免费
    if vip_level >= 5:
        # 创建免费购买记录
        purchase = VideoPurchase(
            user_id=current_user.id,
            video_id=video_id,
            coins_paid=0,
            original_price=coin_price,
            discount_info=f"VIP{vip_level}会员免费"
        )
        db.add(purchase)
        await db.commit()
        return {"message": "VIP会员免费观看", "coins_paid": 0}
    
    # VIP免费类型
    vip_free_level = getattr(video, 'vip_free_level', 0) or 0
    if pay_type == 'vip_free' and vip_level >= vip_free_level and vip_level > 0:
        purchase = VideoPurchase(
            user_id=current_user.id,
            video_id=video_id,
            coins_paid=0,
            original_price=coin_price,
            discount_info=f"VIP{vip_level}会员免费"
        )
        db.add(purchase)
        await db.commit()
        return {"message": "VIP会员免费观看", "coins_paid": 0}
    
    # 使用统一VIP配置计算折扣
    from app.core.vip_benefits import calculate_discounted_price, get_vip_discount
    discount_rate = get_vip_discount(vip_level)
    final_price = calculate_discounted_price(coin_price, vip_level)
    
    # 扣除金币
    await deduct_coins(
        db,
        current_user.id,
        final_price,
        transaction_type="purchase",
        source_type="video",
        source_id=video_id,
        description=f"购买视频: {video.title[:20]}"
    )
    
    # 创建购买记录
    discount_info = None
    if discount_rate < 1.0:
        discount_info = f"VIP{vip_level}会员{int(discount_rate*100)}折"
    
    purchase = VideoPurchase(
        user_id=current_user.id,
        video_id=video_id,
        coins_paid=final_price,
        original_price=coin_price,
        discount_info=discount_info
    )
    db.add(purchase)
    
    # 如果视频有创作者，记录收益分成
    if hasattr(video, 'creator_id') and video.creator_id:
        from app.models.creator import Creator, CreatorEarning
        
        creator_result = await db.execute(
            select(Creator).where(Creator.id == video.creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        
        if creator:
            # 计算分成金额（默认创作者70%，平台30%）
            share_ratio = creator.platform_share_ratio or 0.3
            creator_share = final_price * (1 - share_ratio)
            platform_share = final_price * share_ratio
            
            # 记录创作者收益
            earning = CreatorEarning(
                creator_id=creator.id,
                earning_type="video_sale",
                amount=int(creator_share),
                source_id=video_id,
                source_type="video_purchase",
                description=f"视频销售收益: {video.title[:20]}",
                buyer_id=current_user.id,
                total_amount=final_price,
                platform_fee=int(platform_share),
                status="settled"
            )
            db.add(earning)
            
            # 更新创作者可用金币
            creator.available_coins += int(creator_share)
            creator.total_coins_earned += int(creator_share)
    
    await db.commit()
    
    # 获取购买后的余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    balance_after = user_coins.balance if user_coins else 0
    
    return {
        "success": True,
        "message": "购买成功",
        "coins_paid": final_price,
        "original_price": coin_price,
        "discount_info": discount_info,
        "balance_after": balance_after
    }


@router.get("/purchase/video/{video_id}/check")
async def check_video_purchase(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查视频购买状态 - 使用统一视频访问权限服务"""
    from app.services.video_access import check_video_access_by_id
    
    result = await check_video_access_by_id(db, video_id, current_user)
    
    if result is None:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 返回前端需要的格式
    return {
        "can_watch": result.can_watch,
        "is_free": result.is_free,
        "is_purchased": result.is_purchased,
        "is_vip_free": result.is_vip_free,
        "coin_price": result.coin_price,
        "original_price": result.original_price if result.original_price != result.coin_price else None,
        "discount_rate": result.discount_rate,
        "free_preview_seconds": result.free_preview_seconds,
        "user_coins": result.user_coins,
        "vip_level": result.vip_level,
        "vip_name": result.vip_name,
        "reason": result.reason if result.reason else None
    }


@router.get("/purchases")
async def get_user_purchases(
    type: str = Query("video", description="购买类型: video/comic/novel等"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取已购内容列表"""
    from app.models.video import Video
    
    # 目前只支持视频类型
    if type != "video":
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    
    # 计算总数
    count_query = select(func.count()).select_from(VideoPurchase).where(
        VideoPurchase.user_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = select(VideoPurchase, Video).join(
        Video, VideoPurchase.video_id == Video.id
    ).where(
        VideoPurchase.user_id == current_user.id
    ).order_by(VideoPurchase.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    purchases = []
    for purchase, video in result.all():
        purchases.append({
            "id": purchase.id,
            "video_id": video.id,
            "title": video.title,
            "cover_url": video.cover_url,
            "duration": video.duration,
            "price": purchase.coins_paid,
            "purchased_at": purchase.created_at.isoformat() if purchase.created_at else None
        })
    
    return {
        "items": purchases,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== 合集购买相关 ====================

@router.post("/purchase/collection/{collection_id}")
async def purchase_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """购买合集"""
    from app.models.creator import VideoCollection, CollectionVideo, Creator, CreatorEarning
    from app.models.user import UserVIP
    
    # 获取合集
    result = await db.execute(
        select(VideoCollection).where(VideoCollection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    # 检查是否已购买
    existing = await db.execute(
        select(CollectionPurchase).where(
            CollectionPurchase.user_id == current_user.id,
            CollectionPurchase.collection_id == collection_id,
            CollectionPurchase.purchase_type == "full"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已购买过此合集")
    
    coin_price = collection.total_price or 0
    
    if coin_price <= 0:
        raise HTTPException(status_code=400, detail="此合集无需购买")
    
    # 获取用户VIP信息
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == current_user.id))
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    # 黄金至尊和钻石至尊免费
    if vip_level >= 5:
        purchase = CollectionPurchase(
            user_id=current_user.id,
            collection_id=collection_id,
            purchase_type="full",
            coins_paid=0
        )
        db.add(purchase)
        await db.commit()
        return {"success": True, "message": "VIP会员免费观看", "coins_paid": 0}
    
    # 使用统一VIP配置计算折扣
    from app.core.vip_benefits import calculate_discounted_price, get_vip_discount
    discount_rate = get_vip_discount(vip_level)
    final_price = calculate_discounted_price(coin_price, vip_level)
    
    # 扣除金币
    await deduct_coins(
        db,
        current_user.id,
        final_price,
        transaction_type="purchase",
        source_type="collection",
        source_id=collection_id,
        description=f"购买合集: {collection.title[:20]}"
    )
    
    # 创建购买记录
    purchase = CollectionPurchase(
        user_id=current_user.id,
        collection_id=collection_id,
        purchase_type="full",
        coins_paid=final_price
    )
    db.add(purchase)
    
    # 创作者收益分成
    if collection.creator_id:
        creator_result = await db.execute(
            select(Creator).where(Creator.id == collection.creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        
        if creator:
            share_ratio = creator.platform_share_ratio or 0.3
            creator_share = final_price * (1 - share_ratio)
            platform_share = final_price * share_ratio
            
            earning = CreatorEarning(
                creator_id=creator.id,
                earning_type="collection_sale",
                amount=int(creator_share),
                source_id=collection_id,
                source_type="collection_purchase",
                description=f"合集销售收益: {collection.title[:20]}",
                buyer_id=current_user.id,
                total_amount=final_price,
                platform_fee=int(platform_share),
                status="settled"
            )
            db.add(earning)
            
            creator.available_coins += int(creator_share)
            creator.total_coins_earned += int(creator_share)
    
    await db.commit()
    
    # 获取余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    
    return {
        "success": True,
        "message": "购买成功",
        "coins_paid": final_price,
        "balance_after": user_coins.balance if user_coins else 0
    }


@router.get("/purchase/collection/{collection_id}/check")
async def check_collection_purchase(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查合集购买状态"""
    from app.models.creator import VideoCollection
    from app.models.user import UserVIP
    
    # 获取合集
    result = await db.execute(
        select(VideoCollection).where(VideoCollection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    coin_price = collection.total_price or 0
    
    # 免费合集
    if coin_price <= 0:
        return {"purchased": True, "is_free": True}
    
    # 检查VIP
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == current_user.id))
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    if vip_level >= 5:
        return {"purchased": True, "is_free": True, "reason": "VIP会员免费"}
    
    # 检查是否已购买
    existing = await db.execute(
        select(CollectionPurchase).where(
            CollectionPurchase.user_id == current_user.id,
            CollectionPurchase.collection_id == collection_id,
            CollectionPurchase.purchase_type == "full"
        )
    )
    
    if existing.scalar_one_or_none():
        return {"purchased": True, "is_free": False}
    
    # 使用统一VIP配置计算折扣价格
    from app.core.vip_benefits import calculate_discounted_price, get_vip_discount
    discount_rate = get_vip_discount(vip_level)
    final_price = calculate_discounted_price(coin_price, vip_level)
    
    return {
        "purchased": False,
        "is_free": False,
        "coin_price": final_price,
        "original_price": coin_price
    }


"""
金币系统API接口
"""
from datetime import datetime
import uuid
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.coins import (
    UserCoins, CoinTransaction, RechargePackage, RechargeOrder, VideoPurchase
)

router = APIRouter(prefix="/coins", tags=["金币系统"])


# ==================== Schemas ====================

class CoinBalanceResponse(BaseModel):
    balance: int
    total_recharged: int
    total_spent: int
    total_earned: int
    frozen: int

    class Config:
        from_attributes = True


class RechargePackageResponse(BaseModel):
    id: int
    name: str
    coins: int
    bonus_coins: int
    price: float
    original_price: Optional[float] = None
    icon: Optional[str] = None
    tag: Optional[str] = None
    description: Optional[str] = None
    is_hot: bool = False
    is_first_charge: bool = False

    class Config:
        from_attributes = True


class CoinTransactionResponse(BaseModel):
    id: int
    amount: int
    balance_after: int
    transaction_type: str
    source_type: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateRechargeOrderRequest(BaseModel):
    package_id: int
    payment_method: str  # alipay/wechat


class RechargeOrderResponse(BaseModel):
    order_no: str
    coins: int
    bonus_coins: int
    amount: float
    payment_method: str
    status: str
    pay_url: Optional[str] = None  # 支付链接
    qr_code: Optional[str] = None  # 支付二维码

    class Config:
        from_attributes = True


# ==================== Helper Functions ====================

async def get_or_create_user_coins(db: AsyncSession, user_id: int) -> UserCoins:
    """获取或创建用户金币账户"""
    result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == user_id)
    )
    user_coins = result.scalar_one_or_none()
    
    if not user_coins:
        user_coins = UserCoins(user_id=user_id)
        db.add(user_coins)
        await db.commit()
        await db.refresh(user_coins)
    
    return user_coins


async def add_coins(
    db: AsyncSession,
    user_id: int,
    amount: int,
    transaction_type: str,
    source_type: str = None,
    source_id: int = None,
    description: str = None,
    extra_data: dict = None
) -> CoinTransaction:
    """添加金币"""
    user_coins = await get_or_create_user_coins(db, user_id)
    user_coins.balance += amount
    
    if transaction_type == "recharge":
        user_coins.total_recharged += amount
    elif transaction_type == "earn":
        user_coins.total_earned += amount
    
    transaction = CoinTransaction(
        user_id=user_id,
        amount=amount,
        balance_after=user_coins.balance,
        transaction_type=transaction_type,
        source_type=source_type,
        source_id=source_id,
        description=description,
        extra_data=extra_data
    )
    db.add(transaction)
    
    return transaction


async def deduct_coins(
    db: AsyncSession,
    user_id: int,
    amount: int,
    transaction_type: str,
    source_type: str = None,
    source_id: int = None,
    description: str = None,
    extra_data: dict = None
) -> CoinTransaction:
    """扣除金币"""
    user_coins = await get_or_create_user_coins(db, user_id)
    
    if user_coins.balance < amount:
        raise HTTPException(status_code=400, detail="金币余额不足")
    
    user_coins.balance -= amount
    user_coins.total_spent += amount
    
    transaction = CoinTransaction(
        user_id=user_id,
        amount=-amount,
        balance_after=user_coins.balance,
        transaction_type=transaction_type,
        source_type=source_type,
        source_id=source_id,
        description=description,
        extra_data=extra_data
    )
    db.add(transaction)
    
    return transaction


def generate_order_no() -> str:
    """生成订单号"""
    return f"RC{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


# ==================== API Endpoints ====================

@router.get("/balance", response_model=CoinBalanceResponse)
async def get_coin_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取金币余额"""
    user_coins = await get_or_create_user_coins(db, current_user.id)
    return user_coins


@router.get("/packages", response_model=List[RechargePackageResponse])
async def get_recharge_packages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取充值套餐列表"""
    # 检查用户是否有过充值记录
    has_recharged = await db.execute(
        select(func.count(RechargeOrder.id)).where(
            RechargeOrder.user_id == current_user.id,
            RechargeOrder.status == "paid"
        )
    )
    is_first_charge = has_recharged.scalar() == 0
    
    # 获取套餐
    query = select(RechargePackage).where(RechargePackage.is_active == True)
    
    # 如果不是首充，排除首充专享套餐
    if not is_first_charge:
        query = query.where(RechargePackage.is_first_charge == False)
    
    query = query.order_by(RechargePackage.sort_order)
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return [
        RechargePackageResponse(
            id=p.id,
            name=p.name,
            coins=p.coins,
            bonus_coins=p.bonus_coins,
            price=float(p.price),
            original_price=float(p.original_price) if p.original_price else None,
            icon=p.icon,
            tag=p.tag,
            description=p.description,
            is_hot=p.is_hot,
            is_first_charge=p.is_first_charge
        )
        for p in packages
    ]


@router.post("/recharge", response_model=RechargeOrderResponse)
async def create_recharge_order(
    request: Request,
    data: CreateRechargeOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建充值订单"""
    # 获取套餐
    result = await db.execute(
        select(RechargePackage).where(
            RechargePackage.id == data.package_id,
            RechargePackage.is_active == True
        )
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    # 检查首充专享
    if package.is_first_charge:
        has_recharged = await db.execute(
            select(func.count(RechargeOrder.id)).where(
                RechargeOrder.user_id == current_user.id,
                RechargeOrder.status == "paid"
            )
        )
        if has_recharged.scalar() > 0:
            raise HTTPException(status_code=400, detail="首充专享套餐仅限首次充值")
    
    # 创建订单
    order = RechargeOrder(
        order_no=generate_order_no(),
        user_id=current_user.id,
        package_id=package.id,
        coins=package.coins,
        bonus_coins=package.bonus_coins,
        amount=package.price,
        payment_method=data.payment_method,
        inviter_id=current_user.inviter_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # TODO: 调用支付接口生成支付链接
    # 这里返回模拟数据，实际需要对接支付平台
    pay_url = f"/api/v1/coins/pay/{order.order_no}"
    
    return RechargeOrderResponse(
        order_no=order.order_no,
        coins=order.coins,
        bonus_coins=order.bonus_coins,
        amount=float(order.amount),
        payment_method=order.payment_method,
        status=order.status,
        pay_url=pay_url
    )


@router.post("/pay/{order_no}/simulate")
async def simulate_payment(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """模拟支付成功(开发测试用)"""
    result = await db.execute(
        select(RechargeOrder).where(
            RechargeOrder.order_no == order_no,
            RechargeOrder.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单状态异常")
    
    # 更新订单状态
    order.status = "paid"
    order.paid_at = datetime.utcnow()
    order.payment_no = f"SIM{uuid.uuid4().hex[:16].upper()}"
    
    # 添加金币
    total_coins = order.coins + order.bonus_coins
    await add_coins(
        db,
        current_user.id,
        total_coins,
        transaction_type="recharge",
        source_type="recharge",
        source_id=order.id,
        description=f"充值{order.coins}金币" + (f"+赠送{order.bonus_coins}" if order.bonus_coins else "")
    )
    
    await db.commit()
    
    return {
        "message": f"充值成功！获得{total_coins}金币",
        "coins": order.coins,
        "bonus_coins": order.bonus_coins,
        "total": total_coins
    }


@router.get("/transactions", response_model=List[CoinTransactionResponse])
async def get_coin_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取金币交易记录"""
    query = select(CoinTransaction).where(CoinTransaction.user_id == current_user.id)
    
    if transaction_type:
        query = query.where(CoinTransaction.transaction_type == transaction_type)
    
    query = query.order_by(CoinTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions


@router.get("/orders")
async def get_recharge_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取充值订单列表"""
    query = select(RechargeOrder).where(RechargeOrder.user_id == current_user.id)
    
    if status:
        query = query.where(RechargeOrder.status == status)
    
    query = query.order_by(RechargeOrder.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        {
            "order_no": o.order_no,
            "coins": o.coins,
            "bonus_coins": o.bonus_coins,
            "amount": float(o.amount),
            "payment_method": o.payment_method,
            "status": o.status,
            "paid_at": o.paid_at,
            "created_at": o.created_at
        }
        for o in orders
    ]


# ==================== 视频购买相关 ====================

@router.post("/purchase/video/{video_id}")
async def purchase_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """购买视频"""
    from app.models.video import Video
    from app.models.user import UserVIP
    
    # 获取视频
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已购买
    existing = await db.execute(
        select(VideoPurchase).where(
            VideoPurchase.user_id == current_user.id,
            VideoPurchase.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已购买过此视频")
    
    # 检查付费类型
    pay_type = getattr(video, 'pay_type', 'free') or 'free'
    coin_price = getattr(video, 'coin_price', 0) or 0
    
    if pay_type == 'free' or coin_price <= 0:
        raise HTTPException(status_code=400, detail="此视频无需购买")
    
    # 获取用户VIP信息
    vip_result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id)
    )
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    # 黄金至尊(5)和钻石至尊(6)免费
    if vip_level >= 5:
        # 创建免费购买记录
        purchase = VideoPurchase(
            user_id=current_user.id,
            video_id=video_id,
            coins_paid=0,
            original_price=coin_price,
            discount_info=f"VIP{vip_level}会员免费"
        )
        db.add(purchase)
        await db.commit()
        return {"message": "VIP会员免费观看", "coins_paid": 0}
    
    # VIP免费类型
    vip_free_level = getattr(video, 'vip_free_level', 0) or 0
    if pay_type == 'vip_free' and vip_level >= vip_free_level and vip_level > 0:
        purchase = VideoPurchase(
            user_id=current_user.id,
            video_id=video_id,
            coins_paid=0,
            original_price=coin_price,
            discount_info=f"VIP{vip_level}会员免费"
        )
        db.add(purchase)
        await db.commit()
        return {"message": "VIP会员免费观看", "coins_paid": 0}
    
    # 计算VIP折扣
    discount_rates = {
        1: 0.9,   # 普通VIP 9折
        2: 0.85,  # VIP1 8.5折
        3: 0.8,   # VIP2 8折
        4: 0.7,   # VIP3 7折
    }
    discount_rate = discount_rates.get(vip_level, 1.0)
    final_price = int(coin_price * discount_rate)
    
    # 扣除金币
    await deduct_coins(
        db,
        current_user.id,
        final_price,
        transaction_type="purchase",
        source_type="video",
        source_id=video_id,
        description=f"购买视频: {video.title[:20]}"
    )
    
    # 创建购买记录
    discount_info = None
    if discount_rate < 1.0:
        discount_info = f"VIP{vip_level}会员{int(discount_rate*100)}折"
    
    purchase = VideoPurchase(
        user_id=current_user.id,
        video_id=video_id,
        coins_paid=final_price,
        original_price=coin_price,
        discount_info=discount_info
    )
    db.add(purchase)
    
    # 如果视频有创作者，记录收益分成
    if hasattr(video, 'creator_id') and video.creator_id:
        from app.models.creator import Creator, CreatorEarning
        
        creator_result = await db.execute(
            select(Creator).where(Creator.id == video.creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        
        if creator:
            # 计算分成金额（默认创作者70%，平台30%）
            share_ratio = creator.platform_share_ratio or 0.3
            creator_share = final_price * (1 - share_ratio)
            platform_share = final_price * share_ratio
            
            # 记录创作者收益
            earning = CreatorEarning(
                creator_id=creator.id,
                earning_type="video_sale",
                amount=int(creator_share),
                source_id=video_id,
                source_type="video_purchase",
                description=f"视频销售收益: {video.title[:20]}",
                buyer_id=current_user.id,
                total_amount=final_price,
                platform_fee=int(platform_share),
                status="settled"
            )
            db.add(earning)
            
            # 更新创作者可用金币
            creator.available_coins += int(creator_share)
            creator.total_coins_earned += int(creator_share)
    
    await db.commit()
    
    # 获取购买后的余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    balance_after = user_coins.balance if user_coins else 0
    
    return {
        "success": True,
        "message": "购买成功",
        "coins_paid": final_price,
        "original_price": coin_price,
        "discount_info": discount_info,
        "balance_after": balance_after
    }


@router.get("/purchase/video/{video_id}/check")
async def check_video_purchase(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查视频购买状态"""
    from app.models.video import Video
    from app.models.user import UserVIP
    
    # 获取视频
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    pay_type = getattr(video, 'pay_type', 'free') or 'free'
    coin_price = getattr(video, 'coin_price', 0) or 0
    
    # 免费视频
    if pay_type == 'free' or coin_price <= 0:
        return {
            "can_watch": True,
            "is_free": True,
            "is_purchased": False,
            "coin_price": 0
        }
    
    # 检查是否已购买
    existing = await db.execute(
        select(VideoPurchase).where(
            VideoPurchase.user_id == current_user.id,
            VideoPurchase.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        return {
            "can_watch": True,
            "is_free": False,
            "is_purchased": True,
            "coin_price": 0
        }
    
    # 获取VIP信息
    vip_result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id)
    )
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    # 黄金至尊和钻石至尊免费
    if vip_level >= 5:
        return {
            "can_watch": True,
            "is_free": True,
            "is_purchased": False,
            "coin_price": 0,
            "reason": "VIP会员免费"
        }
    
    # VIP免费
    vip_free_level = getattr(video, 'vip_free_level', 0) or 0
    if pay_type == 'vip_free' and vip_level >= vip_free_level and vip_level > 0:
        return {
            "can_watch": True,
            "is_free": True,
            "is_purchased": False,
            "coin_price": 0,
            "reason": "VIP会员免费"
        }
    
    # 计算折扣价格
    discount_rates = {1: 0.9, 2: 0.85, 3: 0.8, 4: 0.7}
    discount_rate = discount_rates.get(vip_level, 1.0)
    final_price = int(coin_price * discount_rate)
    
    return {
        "can_watch": False,
        "is_free": False,
        "is_purchased": False,
        "coin_price": final_price,
        "original_price": coin_price,
        "discount_rate": discount_rate if discount_rate < 1 else None
    }


@router.get("/purchases")
async def get_user_purchases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取已购视频列表"""
    from app.models.video import Video
    
    query = select(VideoPurchase, Video).join(
        Video, VideoPurchase.video_id == Video.id
    ).where(
        VideoPurchase.user_id == current_user.id
    ).order_by(VideoPurchase.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    purchases = []
    for purchase, video in result.all():
        purchases.append({
            "id": purchase.id,
            "video_id": video.id,
            "video_title": video.title,
            "video_cover": video.cover_url,
            "coins_paid": purchase.coins_paid,
            "purchased_at": purchase.created_at
        })
    
    return purchases


# ==================== 合集购买相关 ====================

@router.post("/purchase/collection/{collection_id}")
async def purchase_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """购买合集"""
    from app.models.creator import VideoCollection, CollectionVideo, Creator, CreatorEarning
    from app.models.user import UserVIP
    
    # 获取合集
    result = await db.execute(
        select(VideoCollection).where(VideoCollection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    # 检查是否已购买
    existing = await db.execute(
        select(CollectionPurchase).where(
            CollectionPurchase.user_id == current_user.id,
            CollectionPurchase.collection_id == collection_id,
            CollectionPurchase.purchase_type == "full"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已购买过此合集")
    
    coin_price = collection.total_price or 0
    
    if coin_price <= 0:
        raise HTTPException(status_code=400, detail="此合集无需购买")
    
    # 获取用户VIP信息
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == current_user.id))
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    # 黄金至尊和钻石至尊免费
    if vip_level >= 5:
        purchase = CollectionPurchase(
            user_id=current_user.id,
            collection_id=collection_id,
            purchase_type="full",
            coins_paid=0
        )
        db.add(purchase)
        await db.commit()
        return {"success": True, "message": "VIP会员免费观看", "coins_paid": 0}
    
    # VIP折扣
    discount_rates = {1: 0.9, 2: 0.85, 3: 0.8, 4: 0.7}
    discount_rate = discount_rates.get(vip_level, 1.0)
    final_price = int(coin_price * discount_rate)
    
    # 扣除金币
    await deduct_coins(
        db,
        current_user.id,
        final_price,
        transaction_type="purchase",
        source_type="collection",
        source_id=collection_id,
        description=f"购买合集: {collection.title[:20]}"
    )
    
    # 创建购买记录
    purchase = CollectionPurchase(
        user_id=current_user.id,
        collection_id=collection_id,
        purchase_type="full",
        coins_paid=final_price
    )
    db.add(purchase)
    
    # 创作者收益分成
    if collection.creator_id:
        creator_result = await db.execute(
            select(Creator).where(Creator.id == collection.creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        
        if creator:
            share_ratio = creator.platform_share_ratio or 0.3
            creator_share = final_price * (1 - share_ratio)
            platform_share = final_price * share_ratio
            
            earning = CreatorEarning(
                creator_id=creator.id,
                earning_type="collection_sale",
                amount=int(creator_share),
                source_id=collection_id,
                source_type="collection_purchase",
                description=f"合集销售收益: {collection.title[:20]}",
                buyer_id=current_user.id,
                total_amount=final_price,
                platform_fee=int(platform_share),
                status="settled"
            )
            db.add(earning)
            
            creator.available_coins += int(creator_share)
            creator.total_coins_earned += int(creator_share)
    
    await db.commit()
    
    # 获取余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    
    return {
        "success": True,
        "message": "购买成功",
        "coins_paid": final_price,
        "balance_after": user_coins.balance if user_coins else 0
    }


@router.get("/purchase/collection/{collection_id}/check")
async def check_collection_purchase(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查合集购买状态"""
    from app.models.creator import VideoCollection
    from app.models.user import UserVIP
    
    # 获取合集
    result = await db.execute(
        select(VideoCollection).where(VideoCollection.id == collection_id)
    )
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    coin_price = collection.total_price or 0
    
    # 免费合集
    if coin_price <= 0:
        return {"purchased": True, "is_free": True}
    
    # 检查VIP
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == current_user.id))
    user_vip = vip_result.scalar_one_or_none()
    vip_level = 0
    if user_vip and user_vip.is_active and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        vip_level = user_vip.vip_level or 0
    
    if vip_level >= 5:
        return {"purchased": True, "is_free": True, "reason": "VIP会员免费"}
    
    # 检查是否已购买
    existing = await db.execute(
        select(CollectionPurchase).where(
            CollectionPurchase.user_id == current_user.id,
            CollectionPurchase.collection_id == collection_id,
            CollectionPurchase.purchase_type == "full"
        )
    )
    
    if existing.scalar_one_or_none():
        return {"purchased": True, "is_free": False}
    
    # 计算折扣价格
    discount_rates = {1: 0.9, 2: 0.85, 3: 0.8, 4: 0.7}
    discount_rate = discount_rates.get(vip_level, 1.0)
    final_price = int(coin_price * discount_rate)
    
    return {
        "purchased": False,
        "is_free": False,
        "coin_price": final_price,
        "original_price": coin_price
    }
