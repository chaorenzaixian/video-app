"""
优惠券系统API
"""
from datetime import datetime, timedelta
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserVIP
from app.models.coupon import (
    CouponTemplate, UserCoupon, NewUserPackage, NewUserPackageClaim, PromotionalEvent
)
from app.models.coins import UserCoins

router = APIRouter(prefix="/coupons", tags=["优惠券系统"])


# ==================== Schemas ====================

class CouponResponse(BaseModel):
    id: int
    coupon_code: str
    name: str
    description: Optional[str]
    coupon_type: str
    discount_type: str
    discount_value: float
    min_amount: float
    status: str
    expire_at: datetime

    class Config:
        from_attributes = True


# ==================== 优惠券领取 ====================

@router.get("/available")
async def get_available_coupons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取可领取的优惠券列表"""
    now = datetime.utcnow()
    
    # 获取所有有效的优惠券模板
    query = select(CouponTemplate).where(
        CouponTemplate.is_active == True,
        CouponTemplate.start_time <= now,
        CouponTemplate.end_time >= now
    )
    result = await db.execute(query)
    templates = result.scalars().all()
    
    available = []
    for tpl in templates:
        # 检查库存
        if tpl.remaining_quantity == 0:
            continue
        
        # 检查用户领取次数
        claimed_count = await db.execute(
            select(func.count(UserCoupon.id)).where(
                UserCoupon.user_id == current_user.id,
                UserCoupon.template_id == tpl.id
            )
        )
        if claimed_count.scalar() >= tpl.per_user_limit:
            continue
        
        available.append({
            "id": tpl.id,
            "name": tpl.name,
            "description": tpl.description,
            "coupon_type": tpl.coupon_type,
            "discount_type": tpl.discount_type,
            "discount_value": float(tpl.discount_value),
            "min_amount": float(tpl.min_amount) if tpl.min_amount else 0,
            "end_time": tpl.end_time
        })
    
    return available


@router.post("/claim/{template_id}")
async def claim_coupon(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取优惠券"""
    now = datetime.utcnow()
    
    # 获取模板
    result = await db.execute(
        select(CouponTemplate).where(CouponTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template or not template.is_active:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    if template.start_time and template.start_time > now:
        raise HTTPException(status_code=400, detail="活动未开始")
    
    if template.end_time and template.end_time < now:
        raise HTTPException(status_code=400, detail="活动已结束")
    
    if template.remaining_quantity == 0:
        raise HTTPException(status_code=400, detail="优惠券已领完")
    
    # 检查领取次数
    claimed_count = await db.execute(
        select(func.count(UserCoupon.id)).where(
            UserCoupon.user_id == current_user.id,
            UserCoupon.template_id == template_id
        )
    )
    if claimed_count.scalar() >= template.per_user_limit:
        raise HTTPException(status_code=400, detail="已达领取上限")
    
    # 计算过期时间
    if template.valid_days:
        expire_at = now + timedelta(days=template.valid_days)
    else:
        expire_at = template.end_time
    
    # 生成优惠券码
    coupon_code = f"C{uuid.uuid4().hex[:8].upper()}"
    
    # 创建用户优惠券
    coupon = UserCoupon(
        user_id=current_user.id,
        template_id=template_id,
        coupon_code=coupon_code,
        expire_at=expire_at
    )
    db.add(coupon)
    
    # 减少库存
    if template.remaining_quantity > 0:
        template.remaining_quantity -= 1
    
    await db.commit()
    
    return {
        "message": "领取成功",
        "coupon_code": coupon_code,
        "expire_at": expire_at
    }


@router.get("/my", response_model=List[CouponResponse])
async def get_my_coupons(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的优惠券"""
    query = select(UserCoupon, CouponTemplate).join(
        CouponTemplate, UserCoupon.template_id == CouponTemplate.id
    ).where(UserCoupon.user_id == current_user.id)
    
    if status:
        if status == "valid":
            query = query.where(
                UserCoupon.status == "unused",
                UserCoupon.expire_at > datetime.utcnow()
            )
        else:
            query = query.where(UserCoupon.status == status)
    
    query = query.order_by(UserCoupon.created_at.desc())
    result = await db.execute(query)
    
    coupons = []
    for coupon, template in result.all():
        # 自动更新过期状态
        if coupon.status == "unused" and coupon.expire_at < datetime.utcnow():
            coupon.status = "expired"
        
        coupons.append(CouponResponse(
            id=coupon.id,
            coupon_code=coupon.coupon_code,
            name=template.name,
            description=template.description,
            coupon_type=template.coupon_type,
            discount_type=template.discount_type,
            discount_value=float(template.discount_value),
            min_amount=float(template.min_amount) if template.min_amount else 0,
            status=coupon.status,
            expire_at=coupon.expire_at
        ))
    
    await db.commit()  # 保存过期状态更新
    
    return coupons


# ==================== 优惠券使用 ====================

@router.post("/use")
async def use_coupon(
    coupon_code: str,
    order_type: str,  # recharge, video, collection
    order_amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """使用优惠券（计算折扣）"""
    now = datetime.utcnow()
    
    # 获取优惠券
    result = await db.execute(
        select(UserCoupon, CouponTemplate).join(
            CouponTemplate, UserCoupon.template_id == CouponTemplate.id
        ).where(
            UserCoupon.coupon_code == coupon_code,
            UserCoupon.user_id == current_user.id
        )
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    
    coupon, template = row
    
    if coupon.status != "unused":
        raise HTTPException(status_code=400, detail="优惠券已使用或已过期")
    
    if coupon.expire_at < now:
        coupon.status = "expired"
        await db.commit()
        raise HTTPException(status_code=400, detail="优惠券已过期")
    
    # 检查优惠券类型
    if template.coupon_type != "all" and template.coupon_type != order_type:
        raise HTTPException(status_code=400, detail=f"此优惠券不适用于{order_type}")
    
    # 检查最低金额
    if template.min_amount and order_amount < float(template.min_amount):
        raise HTTPException(status_code=400, detail=f"订单金额需满{template.min_amount}元")
    
    # 计算折扣
    discount_amount = 0.0
    if template.discount_type == "fixed":
        # 固定金额减免
        discount_amount = float(template.discount_value)
    elif template.discount_type == "percent":
        # 百分比折扣
        discount_amount = order_amount * float(template.discount_value) / 100
        # 检查最大折扣限制
        if template.max_discount and discount_amount > float(template.max_discount):
            discount_amount = float(template.max_discount)
    
    # 确保不会超过订单金额
    discount_amount = min(discount_amount, order_amount)
    final_amount = order_amount - discount_amount
    
    return {
        "valid": True,
        "coupon_code": coupon_code,
        "discount_type": template.discount_type,
        "discount_value": float(template.discount_value),
        "discount_amount": round(discount_amount, 2),
        "original_amount": order_amount,
        "final_amount": round(final_amount, 2)
    }


@router.post("/confirm-use/{coupon_id}")
async def confirm_use_coupon(
    coupon_id: int,
    order_id: str,
    order_type: str,
    discount_amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """确认使用优惠券（订单完成后调用）"""
    result = await db.execute(
        select(UserCoupon).where(
            UserCoupon.id == coupon_id,
            UserCoupon.user_id == current_user.id,
            UserCoupon.status == "unused"
        )
    )
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在或已使用")
    
    # 标记为已使用
    coupon.status = "used"
    coupon.used_at = datetime.utcnow()
    coupon.used_order_id = order_id
    coupon.used_order_type = order_type
    coupon.used_discount = discount_amount
    
    await db.commit()
    
    return {"message": "优惠券已使用"}


# ==================== 新用户礼包 ====================

@router.get("/new-user-package")
async def get_new_user_package(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取新用户礼包信息"""
    # 检查是否已领取
    claimed = await db.execute(
        select(NewUserPackageClaim).where(
            NewUserPackageClaim.user_id == current_user.id
        )
    )
    if claimed.scalar_one_or_none():
        return {"claimed": True, "package": None}
    
    # 获取当前有效的礼包
    result = await db.execute(
        select(NewUserPackage).where(NewUserPackage.is_active == True).limit(1)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        return {"claimed": False, "package": None}
    
    return {
        "claimed": False,
        "package": {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "contents": package.contents
        }
    }


@router.post("/new-user-package/claim")
async def claim_new_user_package(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """领取新用户礼包"""
    # 检查是否已领取
    claimed = await db.execute(
        select(NewUserPackageClaim).where(
            NewUserPackageClaim.user_id == current_user.id
        )
    )
    if claimed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已领取过新用户礼包")
    
    # 获取礼包
    result = await db.execute(
        select(NewUserPackage).where(NewUserPackage.is_active == True).limit(1)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(status_code=404, detail="暂无可领取的礼包")
    
    contents = package.contents or {}
    rewards = []
    
    # 发放金币
    if contents.get("coins"):
        coins_amount = contents["coins"]
        coins_result = await db.execute(
            select(UserCoins).where(UserCoins.user_id == current_user.id)
        )
        user_coins = coins_result.scalar_one_or_none()
        if not user_coins:
            user_coins = UserCoins(user_id=current_user.id)
            db.add(user_coins)
        user_coins.balance += coins_amount
        rewards.append(f"{coins_amount}金币")
    
    # 发放VIP天数
    if contents.get("vip_days"):
        vip_days = contents["vip_days"]
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        user_vip = vip_result.scalar_one_or_none()
        if user_vip:
            if user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
                user_vip.expire_date += timedelta(days=vip_days)
            else:
                user_vip.expire_date = datetime.utcnow() + timedelta(days=vip_days)
            user_vip.is_active = True
        else:
            user_vip = UserVIP(
                user_id=current_user.id,
                vip_level=1,
                is_active=True,
                expire_date=datetime.utcnow() + timedelta(days=vip_days)
            )
            db.add(user_vip)
        rewards.append(f"{vip_days}天VIP")
    
    # 发放优惠券
    if contents.get("coupons"):
        for template_id in contents["coupons"]:
            coupon = UserCoupon(
                user_id=current_user.id,
                template_id=template_id,
                coupon_code=f"N{uuid.uuid4().hex[:8].upper()}",
                expire_at=datetime.utcnow() + timedelta(days=30)
            )
            db.add(coupon)
        rewards.append(f"{len(contents['coupons'])}张优惠券")
    
    # 记录领取
    claim = NewUserPackageClaim(
        user_id=current_user.id,
        package_id=package.id
    )
    db.add(claim)
    
    await db.commit()
    
    return {
        "message": "领取成功",
        "rewards": rewards
    }


# ==================== 促销活动 ====================

@router.get("/events")
async def get_active_events(db: AsyncSession = Depends(get_db)):
    """获取进行中的促销活动"""
    now = datetime.utcnow()
    
    result = await db.execute(
        select(PromotionalEvent).where(
            PromotionalEvent.is_active == True,
            PromotionalEvent.start_time <= now,
            PromotionalEvent.end_time >= now
        ).order_by(PromotionalEvent.start_time)
    )
    
    return [
        {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "event_type": e.event_type,
            "config": e.config,
            "start_time": e.start_time,
            "end_time": e.end_time
        }
        for e in result.scalars().all()
    ]

