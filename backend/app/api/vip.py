"""
VIP会员卡和特权API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import os

from app.core.database import get_db
from app.models.vip import VipCard, VipPrivilege, VipPurchaseRecord
from app.models.user import User
from app.api.deps import get_current_user, get_admin_user
from pydantic import BaseModel

router = APIRouter(prefix="/vip", tags=["VIP会员"])


# ============ Schemas ============

class VipCardResponse(BaseModel):
    id: int
    level: int
    name: str
    display_title: Optional[str] = None
    background_image: Optional[str] = None
    badge_text: Optional[str] = None
    privilege_ids: List[int] = []  # 关联的特权ID列表
    price: float
    original_price: Optional[float] = None
    duration_days: int
    sort_order: int
    is_active: bool = True

    class Config:
        from_attributes = True


class VipPrivilegeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    min_level: int
    sort_order: int

    class Config:
        from_attributes = True


class VipCardCreate(BaseModel):
    level: int = 1
    name: str
    display_title: Optional[str] = None
    background_image: Optional[str] = None
    badge_text: Optional[str] = None
    privilege_ids: List[int] = []  # 关联的特权ID列表
    price: float
    original_price: Optional[float] = None
    duration_days: int = 30
    sort_order: int = 0
    is_active: bool = True


class VipCardUpdate(BaseModel):
    level: Optional[int] = None
    name: Optional[str] = None
    display_title: Optional[str] = None
    background_image: Optional[str] = None
    badge_text: Optional[str] = None
    privilege_ids: Optional[List[int]] = None  # 关联的特权ID列表
    price: Optional[float] = None
    original_price: Optional[float] = None
    duration_days: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class VipPrivilegeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    min_level: int = 1
    privilege_key: Optional[str] = None
    privilege_value: Optional[str] = None
    sort_order: int = 0


class VipPrivilegeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    min_level: Optional[int] = None
    privilege_key: Optional[str] = None
    privilege_value: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PurchaseRequest(BaseModel):
    card_id: int
    payment_method: str = "alipay"


# ============ 用户端API ============

@router.get("/cards", response_model=List[VipCardResponse])
async def get_vip_cards(db: AsyncSession = Depends(get_db)):
    """获取VIP卡片列表"""
    result = await db.execute(
        select(VipCard)
        .where(VipCard.is_active == True)
        .order_by(VipCard.sort_order)
    )
    cards = result.scalars().all()
    # 处理旧数据中privilege_ids可能为None的情况
    return [
        {
            **{k: v for k, v in card.__dict__.items() if not k.startswith('_')},
            "privilege_ids": card.privilege_ids or []
        }
        for card in cards
    ]


@router.get("/privileges", response_model=List[VipPrivilegeResponse])
async def get_vip_privileges(db: AsyncSession = Depends(get_db)):
    """获取VIP特权列表"""
    result = await db.execute(
        select(VipPrivilege)
        .where(VipPrivilege.is_active == True)
        .order_by(VipPrivilege.sort_order)
    )
    return result.scalars().all()


@router.get("/records")
async def get_purchase_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户购买记录"""
    result = await db.execute(
        select(VipPurchaseRecord)
        .where(VipPurchaseRecord.user_id == current_user.id)
        .order_by(VipPurchaseRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("/purchase")
async def purchase_vip(
    data: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """购买VIP"""
    # 获取卡片
    result = await db.execute(
        select(VipCard).where(VipCard.id == data.card_id, VipCard.is_active == True)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="VIP卡片不存在")
    
    # 创建订单
    order_no = f"VIP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    record = VipPurchaseRecord(
        user_id=current_user.id,
        card_id=card.id,
        card_name=card.name,
        amount=card.price,
        duration_days=card.duration_days,
        order_no=order_no,
        payment_method=data.payment_method,
        status="pending"
    )
    db.add(record)
    await db.commit()
    
    return {
        "order_no": order_no,
        "amount": card.price,
        "card_name": card.name
    }


@router.post("/pay/{order_no}/simulate")
async def simulate_pay(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """模拟支付（测试用）"""
    from app.models.user import UserVIP
    
    # 获取订单
    result = await db.execute(
        select(VipPurchaseRecord)
        .where(
            VipPurchaseRecord.order_no == order_no,
            VipPurchaseRecord.user_id == current_user.id
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if record.status == "paid":
        raise HTTPException(status_code=400, detail="订单已支付")
    
    # 更新订单状态
    record.status = "paid"
    record.paid_at = datetime.utcnow()
    
    # 获取卡片信息
    card_result = await db.execute(
        select(VipCard).where(VipCard.id == record.card_id)
    )
    card = card_result.scalar_one_or_none()
    
    # 更新用户VIP信息
    if card:
        # 获取或创建UserVIP记录
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        user_vip = vip_result.scalar_one_or_none()
        
        if card.duration_days == 0:
            # 永久VIP
            new_expire = datetime(2099, 12, 31)
        else:
            # 计算到期时间（叠加）
            if user_vip and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
                new_expire = user_vip.expire_date + timedelta(days=card.duration_days)
            else:
                new_expire = datetime.utcnow() + timedelta(days=card.duration_days)
        
        if user_vip:
            # 更新现有VIP记录
            user_vip.vip_level = max(user_vip.vip_level or 0, card.level)
            user_vip.is_active = True
            user_vip.expire_date = new_expire
            user_vip.total_days = (user_vip.total_days or 0) + card.duration_days
            if not user_vip.start_date:
                user_vip.start_date = datetime.utcnow()
        else:
            # 创建新的VIP记录
            user_vip = UserVIP(
                user_id=current_user.id,
                vip_level=card.level,
                is_active=True,
                start_date=datetime.utcnow(),
                expire_date=new_expire,
                total_days=card.duration_days
            )
            db.add(user_vip)
    
    await db.commit()
    
    return {
        "message": "支付成功，VIP已开通！",
        "vip_level": card.level if card else 0,
        "expire_date": new_expire.isoformat() if card else None
    }


# ============ 管理端API ============

@router.get("/admin/cards")
async def admin_get_cards(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """管理员获取所有VIP卡片"""
    result = await db.execute(
        select(VipCard).order_by(VipCard.sort_order)
    )
    cards = result.scalars().all()
    # 处理旧数据中privilege_ids可能为None的情况
    return [
        {
            **{k: v for k, v in card.__dict__.items() if not k.startswith('_')},
            "privilege_ids": card.privilege_ids or []
        }
        for card in cards
    ]


@router.post("/admin/cards")
async def admin_create_card(
    data: VipCardCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建VIP卡片"""
    card = VipCard(**data.model_dump())
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.put("/admin/cards/{card_id}")
async def admin_update_card(
    card_id: int,
    data: VipCardUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新VIP卡片"""
    result = await db.execute(select(VipCard).where(VipCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(card, key, value)
    
    await db.commit()
    await db.refresh(card)
    return card


@router.delete("/admin/cards/{card_id}")
async def admin_delete_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除VIP卡片"""
    result = await db.execute(select(VipCard).where(VipCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    
    await db.delete(card)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/admin/privileges")
async def admin_get_privileges(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """管理员获取所有VIP特权"""
    result = await db.execute(
        select(VipPrivilege).order_by(VipPrivilege.sort_order)
    )
    return result.scalars().all()


@router.post("/admin/privileges")
async def admin_create_privilege(
    data: VipPrivilegeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建VIP特权"""
    privilege = VipPrivilege(**data.model_dump())
    db.add(privilege)
    await db.commit()
    await db.refresh(privilege)
    return privilege


@router.put("/admin/privileges/{privilege_id}")
async def admin_update_privilege(
    privilege_id: int,
    data: VipPrivilegeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新VIP特权"""
    result = await db.execute(select(VipPrivilege).where(VipPrivilege.id == privilege_id))
    privilege = result.scalar_one_or_none()
    if not privilege:
        raise HTTPException(status_code=404, detail="特权不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(privilege, key, value)
    
    await db.commit()
    await db.refresh(privilege)
    return privilege


@router.delete("/admin/privileges/{privilege_id}")
async def admin_delete_privilege(
    privilege_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除VIP特权"""
    result = await db.execute(select(VipPrivilege).where(VipPrivilege.id == privilege_id))
    privilege = result.scalar_one_or_none()
    if not privilege:
        raise HTTPException(status_code=404, detail="特权不存在")
    
    await db.delete(privilege)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/admin/upload-image")
async def upload_vip_image(
    file: UploadFile = File(...),
    image_type: str = Query(..., description="card 或 privilege"),
    admin: User = Depends(get_admin_user)
):
    """上传VIP卡片或特权图片（自动转WebP优化）"""
    from app.services.image_service import ImageService
    from app.core.config import settings
    
    # 验证文件类型
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    content = await file.read()
    
    # 验证图片
    valid, error = ImageService.validate_image(content, file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        result = await ImageService.save_image(
            content=content,
            subdir=f"vip/{image_type}s",
            filename=f"{image_type}_{uuid.uuid4().hex[:12]}",
            convert_webp=True
        )
        return {"url": result["url"], "optimized": ImageService.is_available()}
    except Exception:
        # 降级处理
        ext = file.filename.split(".")[-1] if "." in file.filename else "webp"
        filename = f"{image_type}_{uuid.uuid4().hex[:12]}.{ext}"
        save_dir = os.path.join(settings.UPLOAD_DIR, "vip", f"{image_type}s")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        return {"url": f"/uploads/vip/{image_type}s/{filename}", "optimized": False}



















