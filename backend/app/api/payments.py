"""
支付相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User, UserVIP, VIPType
from app.models.payment import PaymentOrder, Payment, PaymentStatus, PaymentMethod, OrderType
from app.schemas.payment import CreateOrder, OrderResponse, VIPPriceResponse, OrderListResponse

router = APIRouter()


def get_vip_price(order_type: OrderType) -> int:
    """获取VIP价格（分）"""
    prices = {
        OrderType.VIP_MONTHLY: settings.VIP_PRICE_MONTHLY,
        OrderType.VIP_QUARTERLY: settings.VIP_PRICE_QUARTERLY,
        OrderType.VIP_YEARLY: settings.VIP_PRICE_YEARLY,
        OrderType.VIP_LIFETIME: settings.VIP_PRICE_LIFETIME,
    }
    return prices.get(order_type, 0)


def get_vip_days(order_type: OrderType) -> int:
    """获取VIP天数"""
    days = {
        OrderType.VIP_MONTHLY: 30,
        OrderType.VIP_QUARTERLY: 90,
        OrderType.VIP_YEARLY: 365,
        OrderType.VIP_LIFETIME: 36500,  # 100年
    }
    return days.get(order_type, 0)


@router.get("/prices", response_model=VIPPriceResponse)
async def get_vip_prices():
    """获取VIP价格列表"""
    return VIPPriceResponse(
        monthly=Decimal(settings.VIP_PRICE_MONTHLY) / 100,
        quarterly=Decimal(settings.VIP_PRICE_QUARTERLY) / 100,
        yearly=Decimal(settings.VIP_PRICE_YEARLY) / 100,
        lifetime=Decimal(settings.VIP_PRICE_LIFETIME) / 100,
        currency="CNY"
    )


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_in: CreateOrder,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建支付订单"""
    # 生成订单号
    order_no = f"VOD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    # 获取价格
    amount_cents = get_vip_price(order_in.order_type)
    amount = Decimal(amount_cents) / 100
    
    # 创建订单
    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        order_type=order_in.order_type,
        amount=amount,
        payment_method=order_in.payment_method,
        status=PaymentStatus.PENDING,
        expire_at=datetime.utcnow() + timedelta(hours=2)  # 2小时过期
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # 生成支付链接（这里需要根据实际支付方式生成）
    pay_url = None
    if order_in.payment_method == PaymentMethod.STRIPE:
        # TODO: 调用Stripe API创建支付会话
        pay_url = f"/api/payments/stripe/checkout/{order.order_no}"
    elif order_in.payment_method == PaymentMethod.ALIPAY:
        # TODO: 调用支付宝API创建支付
        pay_url = f"/api/payments/alipay/checkout/{order.order_no}"
    elif order_in.payment_method == PaymentMethod.WECHAT:
        # TODO: 调用微信支付API创建支付
        pay_url = f"/api/payments/wechat/checkout/{order.order_no}"
    
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        order_type=order.order_type,
        amount=order.amount,
        currency=order.currency,
        status=order.status,
        payment_method=order.payment_method,
        pay_url=pay_url,
        created_at=order.created_at,
        expire_at=order.expire_at
    )


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表"""
    from sqlalchemy import func, desc
    
    query = select(PaymentOrder).where(PaymentOrder.user_id == current_user.id)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页
    query = query.order_by(desc(PaymentOrder.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    items = [
        OrderResponse(
            id=order.id,
            order_no=order.order_no,
            order_type=order.order_type,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            payment_method=order.payment_method,
            created_at=order.created_at,
            expire_at=order.expire_at
        )
        for order in orders
    ]
    
    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/orders/{order_no}", response_model=OrderResponse)
async def get_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单详情"""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    return OrderResponse(
        id=order.id,
        order_no=order.order_no,
        order_type=order.order_type,
        amount=order.amount,
        currency=order.currency,
        status=order.status,
        payment_method=order.payment_method,
        created_at=order.created_at,
        expire_at=order.expire_at
    )


@router.post("/callback/{payment_method}")
async def payment_callback(
    payment_method: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """支付回调"""
    # 获取回调数据
    body = await request.body()
    
    # TODO: 验证签名，解析回调数据
    # 这里需要根据不同的支付方式实现不同的验证逻辑
    
    # 模拟获取订单号
    # order_no = parsed_data.get("order_no")
    # trade_no = parsed_data.get("trade_no")
    
    # 查找订单并处理
    # ...
    
    return {"status": "success"}


async def process_payment_success(
    order: PaymentOrder,
    trade_no: str,
    db: AsyncSession
):
    """处理支付成功"""
    # 更新订单状态
    order.status = PaymentStatus.SUCCESS
    order.trade_no = trade_no
    order.paid_at = datetime.utcnow()
    
    # 创建支付记录
    payment = Payment(
        order_id=order.id,
        amount=order.amount,
        payment_method=order.payment_method,
        trade_no=trade_no,
        status=PaymentStatus.SUCCESS
    )
    db.add(payment)
    
    # 更新用户VIP
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == order.user_id)
    )
    vip = result.scalar_one_or_none()
    
    if not vip:
        vip = UserVIP(user_id=order.user_id)
        db.add(vip)
    
    # 计算VIP时长
    days = get_vip_days(order.order_type)
    vip_type_map = {
        OrderType.VIP_MONTHLY: VIPType.MONTHLY,
        OrderType.VIP_QUARTERLY: VIPType.QUARTERLY,
        OrderType.VIP_YEARLY: VIPType.YEARLY,
        OrderType.VIP_LIFETIME: VIPType.LIFETIME,
    }
    
    now = datetime.utcnow()
    
    # 如果当前VIP未过期，在原有基础上续期
    if vip.expire_date and vip.expire_date > now:
        vip.expire_date = vip.expire_date + timedelta(days=days)
    else:
        vip.start_date = now
        vip.expire_date = now + timedelta(days=days)
    
    vip.vip_type = vip_type_map.get(order.order_type)
    vip.is_active = True
    vip.total_days += days
    
    # 设置VIP等级（根据购买类型）
    vip_level_map = {
        OrderType.VIP_MONTHLY: 1,    # 月度会员 = 等级1
        OrderType.VIP_QUARTERLY: 2,  # 季度会员 = 等级2
        OrderType.VIP_YEARLY: 3,     # 年度会员 = 等级3
        OrderType.VIP_LIFETIME: 6,   # 永久会员 = 等级6（最高）
    }
    new_level = vip_level_map.get(order.order_type, 1)
    # 只升不降
    if new_level > (vip.vip_level or 0):
        vip.vip_level = new_level
    
    # ========== 处理代理佣金 ==========
    await process_agent_commission(order.user_id, order.id, order.amount, db)
    
    await db.commit()


async def process_agent_commission(
    user_id: int,
    order_id: int,
    order_amount: float,
    db: AsyncSession
):
    """处理代理佣金"""
    from app.models.promotion import UserProfile, Invitation, Commission, Reward
    from decimal import Decimal
    
    # 查找用户的邀请人
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    user_profile = result.scalar_one_or_none()
    
    if not user_profile or not user_profile.inviter_id:
        return  # 没有邀请人，不处理佣金
    
    # 获取或创建邀请人的推广资料
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_profile.inviter_id)
    )
    inviter_profile = result.scalar_one_or_none()
    
    if not inviter_profile:
        # 为邀请人创建推广资料（基于用户ID生成唯一邀请码）
        from app.core.invite_code import encode_user_id
        invite_code = encode_user_id(user_profile.inviter_id)
        
        inviter_profile = UserProfile(
            user_id=user_profile.inviter_id,
            invite_code=invite_code
        )
        db.add(inviter_profile)
        await db.flush()
    
    if inviter_profile.agent_level == 0:
        # 邀请人不是代理，但仍可获得充值奖励VIP
        pass
    else:
        # 计算佣金
        commission_rate = inviter_profile.commission_rate
        commission_amount = Decimal(str(order_amount)) * commission_rate
        
        # 创建佣金记录
        commission = Commission(
            agent_id=user_profile.inviter_id,
            from_user_id=user_id,
            order_id=order_id,
            order_amount=Decimal(str(order_amount)),
            commission_type="direct",
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            level_diff=1,
            status="settled"  # 直接结算
        )
        db.add(commission)
        
        # 更新代理余额
        inviter_profile.total_commission += commission_amount
        inviter_profile.available_balance += commission_amount
    
    # 检查是否首次充值，发放充值奖励
    result = await db.execute(
        select(Invitation).where(
            Invitation.invitee_id == user_id,
            Invitation.inviter_id == user_profile.inviter_id,
            Invitation.recharge_rewarded == False
        )
    )
    invitation = result.scalar_one_or_none()
    
    if invitation:
        # 标记已发放充值奖励
        invitation.recharge_rewarded = True
        invitation.is_valid = True  # 标记为有效邀请（已充值）
        
        # 更新邀请人的有效邀请数
        inviter_profile.valid_invites = (inviter_profile.valid_invites or 0) + 1
        new_valid_invites = inviter_profile.valid_invites
        
        # ========== 自动发放里程碑奖励 ==========
        from app.api.promotion import auto_grant_milestone_rewards
        total_days, milestones = await auto_grant_milestone_rewards(
            db, 
            user_profile.inviter_id, 
            new_valid_invites
        )
        if total_days > 0:
            print(f"[Milestone Reward] User {user_profile.inviter_id} granted {total_days} VIP days for {len(milestones)} milestones")
        
        # ========== 自动升级代理等级 ==========
        from app.services.agent_upgrade import auto_upgrade_agent
        upgraded, new_level, level_name = await auto_upgrade_agent(db, user_profile.inviter_id)
        if upgraded:
            print(f"[Auto Upgrade] User {user_profile.inviter_id} upgraded to level {new_level} ({level_name})")


# ========== 支付宝支付接口 ==========

@router.post("/alipay/create")
async def create_alipay_order(
    order_in: CreateOrder,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建支付宝支付订单"""
    from app.services.payment_service import payment_service
    
    # 生成订单号
    order_no = f"VOD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    # 获取价格
    amount_cents = get_vip_price(order_in.order_type)
    amount = Decimal(amount_cents) / 100
    
    # 创建数据库订单
    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        order_type=order_in.order_type,
        amount=amount,
        payment_method=PaymentMethod.ALIPAY,
        status=PaymentStatus.PENDING,
        expire_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # 调用支付宝创建订单
    subject = f"VOD会员-{order_in.order_type.value}"
    result = await payment_service.create_order(
        provider="alipay",
        order_id=order_no,
        amount=amount_cents,
        subject=subject,
        description=f"VOD平台会员充值"
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "创建支付订单失败"
        )
    
    return {
        "order_no": order_no,
        "amount": float(amount),
        "payment_url": result.payment_url,
        "qr_code": result.qr_code
    }


@router.post("/alipay/notify")
async def alipay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """支付宝异步回调"""
    from app.services.payment_service import payment_service
    
    # 获取回调数据
    form_data = await request.form()
    data = dict(form_data)
    
    # 验证签名
    is_valid, order_no, amount = await payment_service.verify_callback("alipay", data)
    
    if not is_valid:
        return "fail"
    
    # 查找订单
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        return "fail"
    
    if order.status == PaymentStatus.SUCCESS:
        return "success"  # 已处理过
    
    # 处理支付成功
    trade_no = data.get("trade_no", "")
    await process_payment_success(order, trade_no, db)
    
    return "success"


@router.get("/alipay/return")
async def alipay_return(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """支付宝同步回调（页面跳转）"""
    params = dict(request.query_params)
    order_no = params.get("out_trade_no")
    
    # 查询订单状态
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()
    
    if order and order.status == PaymentStatus.SUCCESS:
        return {"status": "success", "message": "支付成功", "order_no": order_no}
    else:
        return {"status": "pending", "message": "支付处理中", "order_no": order_no}


# ========== 微信支付接口 ==========

@router.post("/wechat/create")
async def create_wechat_order(
    order_in: CreateOrder,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建微信支付订单（扫码支付）"""
    from app.services.payment_service import payment_service
    
    # 生成订单号
    order_no = f"VOD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    # 获取价格
    amount_cents = get_vip_price(order_in.order_type)
    amount = Decimal(amount_cents) / 100
    
    # 创建数据库订单
    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        order_type=order_in.order_type,
        amount=amount,
        payment_method=PaymentMethod.WECHAT,
        status=PaymentStatus.PENDING,
        expire_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # 调用微信支付创建订单
    subject = f"VOD会员-{order_in.order_type.value}"
    result = await payment_service.create_order(
        provider="wechat",
        order_id=order_no,
        amount=amount_cents,
        subject=subject
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "创建支付订单失败"
        )
    
    return {
        "order_no": order_no,
        "amount": float(amount),
        "qr_code": result.qr_code  # 微信支付二维码链接
    }


@router.post("/wechat/notify")
async def wechat_notify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """微信支付异步回调"""
    from app.services.payment_service import payment_service
    import json
    
    # 获取回调数据
    body = await request.body()
    data = json.loads(body)
    
    # 验证签名并解密
    is_valid, order_no, amount = await payment_service.verify_callback("wechat", data)
    
    if not is_valid:
        return {"code": "FAIL", "message": "签名验证失败"}
    
    # 查找订单
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        return {"code": "FAIL", "message": "订单不存在"}
    
    if order.status == PaymentStatus.SUCCESS:
        return {"code": "SUCCESS", "message": "OK"}
    
    # 处理支付成功
    trade_no = data.get("resource", {}).get("transaction_id", "")
    await process_payment_success(order, trade_no, db)
    
    return {"code": "SUCCESS", "message": "OK"}


# ========== 订单查询接口 ==========

@router.get("/query/{order_no}")
async def query_payment_status(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查询支付状态"""
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    return {
        "order_no": order.order_no,
        "status": order.status.value,
        "amount": float(order.amount),
        "payment_method": order.payment_method.value,
        "created_at": order.created_at.isoformat(),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None
    }



# ========== 易支付接口 ==========

@router.post("/epay/create")
async def create_epay_order(
    order_in: CreateOrder,
    pay_type: str = "alipay",  # alipay/wxpay/qqpay
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建易支付订单
    
    pay_type: 支付方式
    - alipay: 支付宝
    - wxpay: 微信支付
    - qqpay: QQ钱包
    """
    from app.services.epay_service import epay_service
    
    # 生成订单号
    order_no = f"VOD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    # 获取价格（分转元）
    amount_cents = get_vip_price(order_in.order_type)
    amount = amount_cents / 100
    
    # 获取客户端IP
    client_ip = None
    if request:
        client_ip = request.client.host if request.client else None
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
    
    # 创建数据库订单
    payment_method_map = {
        'alipay': PaymentMethod.ALIPAY,
        'wxpay': PaymentMethod.WECHAT,
        'qqpay': PaymentMethod.ALIPAY,  # QQ钱包暂时归类到支付宝
    }
    
    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        order_type=order_in.order_type,
        amount=Decimal(str(amount)),
        payment_method=payment_method_map.get(pay_type, PaymentMethod.ALIPAY),
        status=PaymentStatus.PENDING,
        expire_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # 调用易支付创建订单
    subject = f"VOD会员-{order_in.order_type.value}"
    result = await epay_service.create_order(
        order_id=order_no,
        amount=amount,
        subject=subject,
        pay_type=pay_type,
        client_ip=client_ip
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "创建支付订单失败"
        )
    
    return {
        "order_no": order_no,
        "amount": amount,
        "payment_url": result.payment_url,
        "qr_code": result.qr_code
    }


@router.post("/epay/create-qr")
async def create_epay_qr_order(
    order_in: CreateOrder,
    pay_type: str = "alipay",
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建易支付订单（获取二维码）
    适用于 APP 内扫码支付
    """
    from app.services.epay_service import epay_service
    
    order_no = f"VOD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    amount_cents = get_vip_price(order_in.order_type)
    amount = amount_cents / 100
    
    client_ip = None
    if request:
        client_ip = request.client.host if request.client else None
    
    payment_method_map = {
        'alipay': PaymentMethod.ALIPAY,
        'wxpay': PaymentMethod.WECHAT,
        'qqpay': PaymentMethod.ALIPAY,
    }
    
    order = PaymentOrder(
        order_no=order_no,
        user_id=current_user.id,
        order_type=order_in.order_type,
        amount=Decimal(str(amount)),
        payment_method=payment_method_map.get(pay_type, PaymentMethod.ALIPAY),
        status=PaymentStatus.PENDING,
        expire_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    subject = f"VOD会员-{order_in.order_type.value}"
    result = await epay_service.create_qr_order(
        order_id=order_no,
        amount=amount,
        subject=subject,
        pay_type=pay_type,
        client_ip=client_ip
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "创建支付订单失败"
        )
    
    return {
        "order_no": order_no,
        "amount": amount,
        "qr_code": result.qr_code,
        "payment_url": result.payment_url
    }


@router.get("/epay/notify")
@router.post("/epay/notify")
async def epay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    易支付异步回调通知
    支持 GET 和 POST 两种方式
    """
    from app.services.epay_service import epay_service
    
    # 获取回调参数
    if request.method == "POST":
        form_data = await request.form()
        params = dict(form_data)
    else:
        params = dict(request.query_params)
    
    print(f"[Epay Notify] Received: {params}")
    
    # 解析并验证回调
    is_success, order_no, trade_no, amount, trade_status = epay_service.parse_callback(params)
    
    if not order_no:
        return "fail"
    
    # 查找订单
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        print(f"[Epay Notify] Order not found: {order_no}")
        return "fail"
    
    # 已处理过
    if order.status == PaymentStatus.SUCCESS:
        return "success"
    
    # 验证金额
    if abs(float(order.amount) - amount) > 0.01:
        print(f"[Epay Notify] Amount mismatch: order={order.amount}, callback={amount}")
        return "fail"
    
    if is_success:
        # 处理支付成功
        await process_payment_success(order, trade_no, db)
        print(f"[Epay Notify] Payment success: {order_no}")
        return "success"
    else:
        print(f"[Epay Notify] Payment not success: {trade_status}")
        return "fail"


@router.get("/epay/return")
async def epay_return(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    易支付同步跳转（用户支付完成后跳转）
    """
    from app.services.epay_service import epay_service
    
    params = dict(request.query_params)
    
    # 验证签名
    if not epay_service.verify_sign(params):
        return {"status": "error", "message": "签名验证失败"}
    
    order_no = params.get('out_trade_no')
    trade_status = params.get('trade_status')
    
    # 查询订单状态
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()
    
    if order and order.status == PaymentStatus.SUCCESS:
        return {
            "status": "success",
            "message": "支付成功",
            "order_no": order_no
        }
    elif trade_status == 'TRADE_SUCCESS':
        return {
            "status": "success",
            "message": "支付成功，正在处理",
            "order_no": order_no
        }
    else:
        return {
            "status": "pending",
            "message": "支付处理中",
            "order_no": order_no
        }


@router.get("/epay/query/{order_no}")
async def query_epay_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查询易支付订单状态"""
    from app.services.epay_service import epay_service
    
    # 先查本地订单
    result = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    # 如果本地已成功，直接返回
    if order.status == PaymentStatus.SUCCESS:
        return {
            "order_no": order_no,
            "status": "success",
            "amount": float(order.amount),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        }
    
    # 查询易支付订单状态
    epay_result = await epay_service.query_order(order_no)
    
    return {
        "order_no": order_no,
        "local_status": order.status.value,
        "epay_status": epay_result.get('status'),
        "amount": float(order.amount),
        "epay_response": epay_result
    }
