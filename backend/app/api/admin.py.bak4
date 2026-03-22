"""
管理后台API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import httpx

from app.core.database import get_db
from app.api.deps import get_admin_user, get_super_admin_user
from app.models.user import User, UserRole, UserVIP, VIPType
from app.models.video import Video, VideoStatus, VideoCategory, VideoTag
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.ad import Advertisement
from app.models.comment import Comment
from app.core.vip_config import VIP_LEVEL_CONFIG, update_vip_level_config, get_vip_level_name


# IP归属地查询函数
async def get_ip_location(ip: str) -> str:
    """查询IP归属地"""
    if not ip or ip in ['127.0.0.1', 'localhost', '::1']:
        return "本地"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 使用免费的IP查询API
            response = await client.get(f"http://ip-api.com/json/{ip}?lang=zh-CN")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country', '')
                    region = data.get('regionName', '')
                    city = data.get('city', '')
                    if country == '中国':
                        return f"{region} {city}".strip()
                    return f"{country} {region}".strip()
    except Exception:
        pass
    
    return "未知"

router = APIRouter()


# ========== 数据统计 ==========

class DashboardStats(BaseModel):
    total_users: int
    total_vip_users: int
    total_videos: int
    total_revenue: float
    new_users_today: int
    new_videos_today: int
    active_users_today: int


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表盘统计"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 总用户数
    result = await db.execute(select(func.count()).select_from(User))
    total_users = result.scalar()
    
    # VIP用户数
    result = await db.execute(
        select(func.count()).select_from(UserVIP).where(
            UserVIP.is_active == True,
            UserVIP.expire_date > datetime.utcnow()
        )
    )
    total_vip_users = result.scalar()
    
    # 总视频数
    result = await db.execute(
        select(func.count()).select_from(Video).where(Video.status == VideoStatus.PUBLISHED)
    )
    total_videos = result.scalar()
    
    # 总收入
    result = await db.execute(
        select(func.sum(PaymentOrder.amount)).where(PaymentOrder.status == PaymentStatus.SUCCESS)
    )
    total_revenue = result.scalar() or 0
    
    # 今日新用户
    result = await db.execute(
        select(func.count()).select_from(User).where(User.created_at >= today_start)
    )
    new_users_today = result.scalar()
    
    # 今日新视频
    result = await db.execute(
        select(func.count()).select_from(Video).where(Video.created_at >= today_start)
    )
    new_videos_today = result.scalar()
    
    # 今日活跃用户
    result = await db.execute(
        select(func.count()).select_from(User).where(User.last_login >= today_start)
    )
    active_users_today = result.scalar()
    
    return DashboardStats(
        total_users=total_users,
        total_vip_users=total_vip_users,
        total_videos=total_videos,
        total_revenue=float(total_revenue),
        new_users_today=new_users_today,
        new_videos_today=new_videos_today,
        active_users_today=active_users_today
    )


# ========== 用户管理 ==========

class UserAdminResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None  # 游客账号可能为空
    phone: Optional[str] = None
    nickname: Optional[str] = None
    role: UserRole
    is_active: bool
    is_vip: bool
    is_guest: bool = False
    vip_level: int = 0  # VIP等级
    vip_level_name: Optional[str] = None  # VIP等级名称
    register_ip: Optional[str] = None
    register_ip_location: Optional[str] = None
    last_login_ip: Optional[str] = None
    last_login_ip_location: Optional[str] = None
    vip_expire_date: Optional[datetime] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    items: List[UserAdminResponse]
    total: int
    page: int
    page_size: int


class UpdateVIPRequest(BaseModel):
    """修改VIP时限请求"""
    expire_date: Optional[datetime] = None  # VIP到期时间
    add_days: Optional[int] = None  # 增加天数
    is_active: Optional[bool] = None  # 是否激活
    vip_level: Optional[int] = None  # VIP等级: 0=非VIP, 1=普通VIP, 2=VIP1, 3=VIP2, 4=VIP3, 5=黄金至尊, 6=蓝色至尊, 7=紫色限定至尊


class UserVIPResponse(BaseModel):
    """用户VIP信息响应"""
    user_id: int
    is_active: bool
    vip_type: Optional[str] = None
    vip_level: int = 0  # VIP等级
    vip_level_name: Optional[str] = None  # VIP等级名称
    start_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    total_days: int = 0


# VIP等级名称使用共享配置 (app.core.vip_config)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,  # 改为字符串，支持guest等非枚举值
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    query = select(User)
    
    if search:
        query = query.where(
            User.username.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%")
        )
    
    if role:
        # 处理特殊的guest筛选
        if role.lower() == 'guest':
            query = query.where(User.is_guest == True)
        else:
            # 数据库role字段是varchar，使用cast转换为字符串比较
            from sqlalchemy import cast, String
            query = query.where(cast(User.role, String) == role.upper())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页
    query = query.order_by(desc(User.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 批量获取所有用户的 VIP 信息（避免 N+1 查询）
    user_ids = [user.id for user in users]
    vip_result = await db.execute(
        select(UserVIP).where(UserVIP.user_id.in_(user_ids))
    )
    vip_map = {vip.user_id: vip for vip in vip_result.scalars().all()}
    
    items = []
    for user in users:
        # 从缓存的 VIP 信息中获取
        vip = vip_map.get(user.id)
        is_vip = bool(vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow())
        vip_expire_date = vip.expire_date if vip else None
        vip_level = getattr(vip, 'vip_level', 0) if vip else 0
        vip_level_name = get_vip_level_name(vip_level)
        
        # IP 归属地：不再实时查询，改为显示 IP 地址（前端可按需查询）
        register_ip = getattr(user, 'register_ip', None)
        last_login_ip = getattr(user, 'last_login_ip', None)
        
        items.append(UserAdminResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            nickname=getattr(user, 'nickname', None),
            role=user.role,
            is_active=user.is_active,
            is_vip=is_vip,
            is_guest=getattr(user, 'is_guest', False),
            vip_level=vip_level,
            vip_level_name=vip_level_name,
            register_ip=register_ip,
            register_ip_location=None,  # 不再实时查询，前端按需查询
            last_login_ip=last_login_ip,
            last_login_ip_location=None,  # 不再实时查询，前端按需查询
            vip_expire_date=vip_expire_date,
            created_at=user.created_at,
            last_login=user.last_login
        ))
    
    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


class UserRoleUpdate(BaseModel):
    role: UserRole


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    current_user: User = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户角色（仅超管）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.role = role_in.role
    await db.commit()
    
    return {"message": "更新成功"}


@router.put("/users/{user_id}/status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """禁用/启用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="无法禁用超级管理员")
    
    user.is_active = not user.is_active
    await db.commit()
    
    return {"message": "操作成功", "is_active": user.is_active}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="无法删除管理员账号")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="无法删除自己的账号")
    
    # 删除关联的VIP记录
    from app.models.user import UserVIP
    await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = vip_result.scalar_one_or_none()
    if vip:
        await db.delete(vip)
    
    # 删除用户
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户已删除"}


@router.get("/users/{user_id}/vip", response_model=UserVIPResponse)
async def get_user_vip(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户VIP信息"""
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取VIP信息
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = vip_result.scalar_one_or_none()
    
    if not vip:
        return UserVIPResponse(
            user_id=user_id,
            is_active=False,
            vip_level=0,
            vip_level_name="非VIP",
            total_days=0
        )
    
    vip_level = getattr(vip, 'vip_level', 0) or 0
    # 计算is_active，确保返回布尔值（避免None）
    is_vip_active = bool(vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow())
    
    return UserVIPResponse(
        user_id=user_id,
        is_active=is_vip_active,
        vip_type=vip.vip_type.value if vip.vip_type else None,
        vip_level=vip_level,
        vip_level_name=get_vip_level_name(vip_level),
        start_date=vip.start_date,
        expire_date=vip.expire_date,
        total_days=vip.total_days or 0
    )


@router.put("/users/{user_id}/vip", response_model=UserVIPResponse)
async def update_user_vip(
    user_id: int,
    vip_data: UpdateVIPRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """修改用户VIP时限和等级"""
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取或创建VIP记录
    vip_result = await db.execute(select(UserVIP).where(UserVIP.user_id == user_id))
    vip = vip_result.scalar_one_or_none()
    
    if not vip:
        vip = UserVIP(user_id=user_id)
        db.add(vip)
    
    # 先更新VIP等级（确保在其他操作之前）
    if vip_data.vip_level is not None:
        vip.vip_level = vip_data.vip_level
        # 如果设置了等级且未激活，自动激活
        if vip_data.vip_level > 0 and not vip.is_active:
            vip.is_active = True
            if not vip.start_date:
                vip.start_date = datetime.utcnow()
    
    # 更新VIP信息
    if vip_data.expire_date is not None:
        vip.expire_date = vip_data.expire_date
        if not vip.start_date:
            vip.start_date = datetime.utcnow()
        vip.is_active = True
        # 设置有效期时，如果等级为0则默认为1
        if (vip.vip_level or 0) == 0:
            vip.vip_level = 1
    
    if vip_data.add_days is not None and vip_data.add_days > 0:
        now = datetime.utcnow()
        if vip.expire_date and vip.expire_date > now:
            vip.expire_date = vip.expire_date + timedelta(days=vip_data.add_days)
        else:
            vip.start_date = now
            vip.expire_date = now + timedelta(days=vip_data.add_days)
        vip.is_active = True
        vip.total_days = (vip.total_days or 0) + vip_data.add_days
        # 增加天数时，如果等级为0则默认为1
        if (vip.vip_level or 0) == 0:
            vip.vip_level = 1
    
    if vip_data.is_active is not None:
        vip.is_active = vip_data.is_active
    
    # 强制确保：如果有有效的到期时间，则激活VIP
    if vip.expire_date and vip.expire_date > datetime.utcnow():
        if not vip.is_active:
            vip.is_active = True
        if (vip.vip_level or 0) == 0:
            vip.vip_level = 1
    
    await db.commit()
    await db.refresh(vip)
    
    vip_level = getattr(vip, 'vip_level', 0) or 0
    # 计算is_active，确保返回布尔值（避免None）
    is_vip_active = bool(vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow())
    
    return UserVIPResponse(
        user_id=user_id,
        is_active=is_vip_active,
        vip_type=vip.vip_type.value if vip.vip_type else None,
        vip_level=vip_level,
        vip_level_name=get_vip_level_name(vip_level),
        start_date=vip.start_date,
        expire_date=vip.expire_date,
        total_days=vip.total_days or 0
    )


@router.get("/ip-location/{ip}")
async def query_ip_location(
    ip: str,
    current_user: User = Depends(get_admin_user)
):
    """查询IP归属地"""
    location = await get_ip_location(ip)
    return {"ip": ip, "location": location}


# ========== VIP等级管理 ==========


class VipLevelResponse(BaseModel):
    level: int
    name: str
    icon: str
    color: str = "#FFD700"  # 等级颜色
    discount: float = 1.0   # 折扣率 (0=免费, 1=无折扣)
    description: str
    # 权益配置
    can_download: bool = False       # 是否可下载
    daily_downloads: int = 0         # 每日下载次数
    ad_free: bool = False            # 是否免广告
    priority_support: bool = False   # 优先客服
    exclusive_content: bool = False  # 专属内容


class VipLevelUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    discount: Optional[float] = None
    description: Optional[str] = None
    # 权益配置
    can_download: Optional[bool] = None
    daily_downloads: Optional[int] = None
    ad_free: Optional[bool] = None
    priority_support: Optional[bool] = None
    exclusive_content: Optional[bool] = None


class UserVipUpdate(BaseModel):
    vip_level: int
    expire_days: Optional[int] = None  # 到期天数，None表示不修改
    is_active: Optional[bool] = None


class VipUserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    vip_level: int
    vip_level_name: str
    is_active: bool
    start_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    total_days: int


@router.get("/vip-levels", response_model=List[VipLevelResponse])
async def get_vip_levels(
    current_user: User = Depends(get_admin_user)
):
    """获取所有VIP等级配置"""
    return [
        VipLevelResponse(
            level=level,
            name=config.get("name", ""),
            icon=config.get("icon", ""),
            color=config.get("color", "#FFD700"),
            discount=config.get("discount", 1.0),
            description=config.get("description", ""),
            can_download=config.get("can_download", False),
            daily_downloads=config.get("daily_downloads", 0),
            ad_free=config.get("ad_free", False),
            priority_support=config.get("priority_support", False),
            exclusive_content=config.get("exclusive_content", False),
        )
        for level, config in VIP_LEVEL_CONFIG.items()
    ]


@router.put("/vip-levels/{level}")
async def update_vip_level(
    level: int,
    update_data: VipLevelUpdate,
    current_user: User = Depends(get_super_admin_user)
):
    """更新VIP等级配置（仅超级管理员）"""
    if level not in VIP_LEVEL_CONFIG:
        raise HTTPException(status_code=404, detail="VIP等级不存在")
    
    # 使用共享函数更新配置（包含所有权益字段）
    update_vip_level_config(
        level,
        name=update_data.name,
        icon=update_data.icon,
        color=update_data.color,
        discount=update_data.discount,
        description=update_data.description,
        can_download=update_data.can_download,
        daily_downloads=update_data.daily_downloads,
        ad_free=update_data.ad_free,
        priority_support=update_data.priority_support,
        exclusive_content=update_data.exclusive_content,
    )
    
    return {"message": "更新成功", "level": VIP_LEVEL_CONFIG[level]}


@router.get("/vip-users", response_model=List[VipUserResponse])
async def get_vip_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    vip_level: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取VIP用户列表"""
    query = select(UserVIP).join(User, UserVIP.user_id == User.id)
    
    if vip_level is not None:
        query = query.where(UserVIP.vip_level == vip_level)
    if is_active is not None:
        query = query.where(UserVIP.is_active == is_active)
    
    query = query.order_by(desc(UserVIP.vip_level), desc(UserVIP.expire_date))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    vip_records = result.scalars().all()
    
    users = []
    for vip in vip_records:
        user_result = await db.execute(select(User).where(User.id == vip.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            users.append(VipUserResponse(
                id=user.id,
                username=user.username,
                nickname=user.nickname,
                avatar=user.avatar,
                vip_level=vip.vip_level or 0,
                vip_level_name=get_vip_level_name(vip.vip_level or 0),
                is_active=vip.is_active,
                start_date=vip.start_date,
                expire_date=vip.expire_date,
                total_days=vip.total_days or 0
            ))
    
    return users


# ========== 视频管理 ==========

class VideoAdminResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    duration: Optional[float] = 0
    status: VideoStatus
    category_id: Optional[int] = None
    short_category_id: Optional[int] = None  # 短视频分类
    coin_price: int = 0  # 价格
    is_vip_only: bool
    is_featured: bool
    is_short: bool = False
    view_count: int
    uploader_name: str
    tags: List[str] = []
    created_at: datetime


class VideoAdminListResponse(BaseModel):
    items: List[VideoAdminResponse]
    total: int
    page: int
    page_size: int


@router.get("/videos", response_model=VideoAdminListResponse)
async def list_videos_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[VideoStatus] = None,
    search: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_short: Optional[bool] = None,
    category_id: Optional[int] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频列表（管理）"""
    from sqlalchemy.orm import selectinload
    
    query = select(Video)
    
    if status:
        query = query.where(Video.status == status)
    
    if search:
        query = query.where(Video.title.ilike(f"%{search}%"))
    
    if is_featured is not None:
        query = query.where(Video.is_featured == is_featured)
    
    if is_short is not None:
        query = query.where(Video.is_short == is_short)
    
    if category_id is not None:
        query = query.where(Video.category_id == category_id)
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # 分页 + 预加载标签
    query = query.options(selectinload(Video.tags))
    query = query.order_by(desc(Video.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    items = []
    for video in videos:
        uploader_result = await db.execute(select(User).where(User.id == video.uploader_id))
        uploader = uploader_result.scalar_one()
        
        items.append(VideoAdminResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            cover_url=video.cover_url,
            duration=video.duration or 0,
            status=video.status,
            category_id=video.category_id,
            short_category_id=video.short_category_id,
            coin_price=video.coin_price or 0,
            is_vip_only=video.is_vip_only or False,
            is_featured=video.is_featured or False,
            is_short=video.is_short or False,
            view_count=video.view_count or 0,
            uploader_name=uploader.nickname or uploader.username,
            tags=[tag.name for tag in video.tags] if video.tags else [],
            created_at=video.created_at
        ))
    
    return VideoAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


# ========== 视频统计和审核 ==========

class VideoPricingStats(BaseModel):
    """视频定价统计"""
    pending: int = 0
    published: int = 0
    paid: int = 0
    vip_only: int = 0


@router.get("/videos/pricing-stats", response_model=VideoPricingStats)
async def get_video_pricing_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频定价统计"""
    # 待审核数量 (REVIEWING 状态)
    result = await db.execute(
        select(func.count()).select_from(Video).where(Video.status == VideoStatus.REVIEWING)
    )
    pending = result.scalar() or 0
    
    # 已发布数量
    result = await db.execute(
        select(func.count()).select_from(Video).where(Video.status == VideoStatus.PUBLISHED)
    )
    published = result.scalar() or 0
    
    # 付费视频数量 (coin_price > 0)
    result = await db.execute(
        select(func.count()).select_from(Video).where(
            Video.status == VideoStatus.PUBLISHED,
            Video.coin_price > 0
        )
    )
    paid = result.scalar() or 0
    
    # VIP专属视频数量
    result = await db.execute(
        select(func.count()).select_from(Video).where(
            Video.status == VideoStatus.PUBLISHED,
            Video.is_vip_only == True
        )
    )
    vip_only = result.scalar() or 0
    
    return VideoPricingStats(
        pending=pending,
        published=published,
        paid=paid,
        vip_only=vip_only
    )


class ReviewQueueItem(BaseModel):
    """审核队列项"""
    id: int
    title: str
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[int] = None
    uploader_name: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReviewQueueResponse(BaseModel):
    """审核队列响应"""
    items: List[ReviewQueueItem]
    total: int
    page: int
    page_size: int


@router.get("/videos/review-queue", response_model=ReviewQueueResponse)
async def get_video_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取待审核视频队列"""
    # 查询待审核视频 (REVIEWING 状态)
    query = select(Video).where(Video.status == VideoStatus.REVIEWING)
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0
    
    # 分页
    query = query.order_by(Video.created_at.asc())  # 先上传的先审核
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    items = []
    for video in videos:
        # 获取上传者信息
        uploader_result = await db.execute(select(User).where(User.id == video.uploader_id))
        uploader = uploader_result.scalar_one_or_none()
        
        items.append(ReviewQueueItem(
            id=video.id,
            title=video.title,
            cover_url=video.cover_url,
            video_url=video.video_url,
            duration=video.duration,
            uploader_name=(uploader.nickname or uploader.username) if uploader else "未知用户",
            created_at=video.created_at
        ))
    
    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


class VideoStatusUpdate(BaseModel):
    status: VideoStatus


@router.put("/videos/{video_id}/status")
async def update_video_status(
    video_id: int,
    status_in: VideoStatusUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新视频状态"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video.status = status_in.status
    if status_in.status == VideoStatus.PUBLISHED:
        video.published_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.put("/videos/{video_id}/featured")
async def toggle_video_featured(
    video_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """设置/取消推荐"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video.is_featured = not video.is_featured
    await db.commit()
    
    return {"message": "操作成功", "is_featured": video.is_featured}


@router.get("/videos/{video_id}")
async def get_video_detail(
    video_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取视频详情"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 获取上传者信息
    uploader_result = await db.execute(select(User).where(User.id == video.uploader_id))
    uploader = uploader_result.scalar_one()
    
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "cover_url": video.cover_url,
        "hls_url": video.hls_url,
        "original_url": video.original_url,
        "duration": video.duration,
        "status": video.status,
        "is_vip_only": video.is_vip_only,
        "is_featured": video.is_featured,
        "view_count": video.view_count,
        "like_count": video.like_count,
        "uploader_name": uploader.nickname or uploader.username,
        "created_at": video.created_at
    }


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_vip_only: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_short: Optional[bool] = None
    category_id: Optional[int] = None
    short_category_id: Optional[int] = None  # 短视频分类
    coin_price: Optional[int] = None
    tags: Optional[List[str]] = None


@router.put("/videos/{video_id}")
async def update_video(
    video_id: int,
    video_in: VideoUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """编辑视频"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Video).where(Video.id == video_id).options(selectinload(Video.tags))
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if video_in.title is not None:
        video.title = video_in.title
    if video_in.description is not None:
        video.description = video_in.description
    if video_in.is_vip_only is not None:
        video.is_vip_only = video_in.is_vip_only
    if video_in.is_featured is not None:
        video.is_featured = video_in.is_featured
    if video_in.is_short is not None:
        video.is_short = video_in.is_short
    if video_in.category_id is not None:
        video.category_id = video_in.category_id
    if video_in.short_category_id is not None:
        video.short_category_id = video_in.short_category_id
    if video_in.coin_price is not None:
        video.coin_price = video_in.coin_price
    
    # 更新标签
    if video_in.tags is not None:
        # 清空现有标签
        video.tags = []
        
        # 添加新标签
        for tag_name in video_in.tags:
            # 查找或创建标签
            tag_result = await db.execute(select(VideoTag).where(VideoTag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                # 创建新标签
                tag = VideoTag(name=tag_name, use_count=0)
                db.add(tag)
                await db.flush()
            
            video.tags.append(tag)
            tag.use_count += 1
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除视频"""
    from sqlalchemy import text
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    try:
        # 使用原生SQL按顺序删除关联数据
        # 1. 删除评论点赞
        await db.execute(text("""
            DELETE FROM comment_likes 
            WHERE comment_id IN (SELECT id FROM comments WHERE video_id = :video_id)
        """), {"video_id": video_id})
        
        # 2. 删除评论
        await db.execute(text("DELETE FROM comments WHERE video_id = :video_id"), {"video_id": video_id})
        
        # 3. 删除观看记录
        await db.execute(text("DELETE FROM video_views WHERE video_id = :video_id"), {"video_id": video_id})
        
        # 4. 删除视频-标签关联
        await db.execute(text("DELETE FROM video_tags_association WHERE video_id = :video_id"), {"video_id": video_id})
        
        # 5. 删除视频
        await db.execute(text("DELETE FROM videos WHERE id = :video_id"), {"video_id": video_id})
        
        await db.commit()
        
        return {"message": "删除成功"}
        
    except Exception as e:
        await db.rollback()
        print(f"删除视频错误: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


class ShortVideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None  # 兼容旧参数
    short_category_id: Optional[int] = None  # 新参数
    original_url: str
    cover_url: Optional[str] = None
    duration: Optional[float] = None
    pay_type: str = "free"  # free/coins/vip_free
    coin_price: int = 0
    is_vip_only: bool = False


@router.post("/shorts")
async def create_short_video(
    data: ShortVideoCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """管理员创建短视频"""
    video = Video(
        title=data.title,
        description=data.description,
        short_category_id=data.short_category_id or data.category_id,  # 优先使用新字段
        uploader_id=current_user.id,
        original_url=data.original_url,
        cover_url=data.cover_url,
        duration=data.duration,
        pay_type=data.pay_type,
        coin_price=data.coin_price,
        is_vip_only=data.is_vip_only,
        is_short=True,
        status=VideoStatus.PUBLISHED  # 管理员直接激活
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    return {
        "message": "短视频创建成功",
        "id": video.id,
        "title": video.title
    }


@router.post("/videos/{video_id}/retry-transcode")
async def retry_video_transcode(
    video_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """重新转码失败的视频"""
    from app.services.video_processor import VideoProcessor
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not video.original_url:
        raise HTTPException(status_code=400, detail="原始视频文件不存在")
    
    # 重置状态为处理中
    video.status = VideoStatus.PROCESSING
    await db.commit()
    
    # 后台重新处理视频
    background_tasks.add_task(
        VideoProcessor.process_video,
        video.id,
        video.original_url
    )
    
    return {"message": "已开始重新转码", "video_id": video_id}


@router.get("/videos/{video_id}/progress")
async def get_video_progress(
    video_id: int,
    current_user: User = Depends(get_admin_user),
):
    """获取单个视频的转码进度"""
    from app.core.redis import RedisCache
    
    try:
        progress = await RedisCache.get(f"video_process:{video_id}")
        return {"video_id": video_id, "progress": int(progress) if progress else 0}
    except:
        return {"video_id": video_id, "progress": 0}


@router.post("/videos/progress/batch")
async def get_videos_progress_batch(
    video_ids: List[int],
    current_user: User = Depends(get_admin_user),
):
    """批量获取视频转码进度"""
    from app.core.redis import RedisCache
    
    result = {}
    for video_id in video_ids:
        try:
            progress = await RedisCache.get(f"video_process:{video_id}")
            result[video_id] = int(progress) if progress else 0
        except:
            result[video_id] = 0
    
    return {"progress": result}


# ========== 分类管理 ==========

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[int] = None
    level: int = 1
    category_type: str = "video"  # video/short/both


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    category_type: Optional[str] = None  # video/short/both


@router.post("/categories")
async def create_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建分类"""
    # 检查分类名是否已存在
    existing = await db.execute(
        select(VideoCategory).where(VideoCategory.name == category_in.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"分类名称 '{category_in.name}' 已存在")
    
    # 如果有父级分类，自动设置level为2
    level = category_in.level
    if category_in.parent_id:
        level = 2
    
    category = VideoCategory(
        name=category_in.name,
        description=category_in.description,
        icon=category_in.icon,
        sort_order=category_in.sort_order,
        category_type=category_in.category_type
    )
    
    # 尝试设置新字段（兼容旧数据库）
    try:
        category.parent_id = category_in.parent_id
        category.level = level
    except Exception:
        pass
    
    db.add(category)
    try:
        await db.commit()
        await db.refresh(category)
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"分类名称 '{category_in.name}' 已存在")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")
    
    return {"id": category.id, "message": "创建成功"}


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新分类"""
    result = await db.execute(select(VideoCategory).where(VideoCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if category_in.name is not None:
        category.name = category_in.name
    if category_in.description is not None:
        category.description = category_in.description
    if category_in.icon is not None:
        category.icon = category_in.icon
    if category_in.sort_order is not None:
        category.sort_order = category_in.sort_order
    if category_in.parent_id is not None:
        category.parent_id = category_in.parent_id
        category.level = 2 if category_in.parent_id else 1
    if category_in.level is not None:
        category.level = category_in.level
    if category_in.category_type is not None:
        category.category_type = category_in.category_type
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除分类（硬删除）"""
    result = await db.execute(select(VideoCategory).where(VideoCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 检查是否有视频使用此分类
    from app.models.video import Video
    video_count_result = await db.execute(
        select(Video).where(Video.category_id == category_id).limit(1)
    )
    if video_count_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该分类下有视频，无法删除。请先移动或删除相关视频。")
    
    # 硬删除 - 真正从数据库删除
    await db.delete(category)
    await db.commit()
    
    return {"message": "删除成功"}


class FeaturedCategoriesUpdate(BaseModel):
    category_ids: List[int]


@router.post("/categories/featured")
async def update_featured_categories(
    data: FeaturedCategoriesUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新推荐分类"""
    # 先将所有分类的is_featured设为False
    await db.execute(
        VideoCategory.__table__.update().values(is_featured=False)
    )
    
    # 将选中的分类设为推荐
    if data.category_ids:
        for cat_id in data.category_ids:
            result = await db.execute(select(VideoCategory).where(VideoCategory.id == cat_id))
            category = result.scalar_one_or_none()
            if category:
                category.is_featured = True
    
    await db.commit()
    
    return {"message": "保存成功"}


# ========== 短视频分类管理 ==========

from app.models.video import ShortVideoCategory


class ShortCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class ShortCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ShortCategoryAdminResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    video_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


@router.get("/short-categories", response_model=List[ShortCategoryAdminResponse])
async def get_all_short_categories(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有短视频分类（包括禁用的）"""
    result = await db.execute(
        select(ShortVideoCategory)
        .order_by(ShortVideoCategory.sort_order.asc(), ShortVideoCategory.id.asc())
    )
    categories = result.scalars().all()
    
    # 获取每个分类的视频数量
    response = []
    for cat in categories:
        count_result = await db.execute(
            select(func.count(Video.id)).where(
                Video.short_category_id == cat.id,
                Video.is_short == True
            )
        )
        video_count = count_result.scalar() or 0
        
        response.append(ShortCategoryAdminResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            icon=cat.icon,
            sort_order=cat.sort_order or 0,
            is_active=cat.is_active if cat.is_active is not None else True,
            video_count=video_count,
            created_at=cat.created_at,
            updated_at=cat.updated_at
        ))
    
    return response


@router.post("/short-categories")
async def create_short_category(
    category_in: ShortCategoryCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建短视频分类"""
    # 检查分类名是否已存在
    existing = await db.execute(
        select(ShortVideoCategory).where(ShortVideoCategory.name == category_in.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"分类名称 '{category_in.name}' 已存在")
    
    category = ShortVideoCategory(
        name=category_in.name,
        description=category_in.description,
        icon=category_in.icon,
        sort_order=category_in.sort_order
    )
    
    db.add(category)
    try:
        await db.commit()
        await db.refresh(category)
    except Exception as e:
        await db.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"分类名称 '{category_in.name}' 已存在")
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")
    
    return {"id": category.id, "message": "创建成功"}


@router.put("/short-categories/{category_id}")
async def update_short_category(
    category_id: int,
    category_in: ShortCategoryUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新短视频分类"""
    result = await db.execute(select(ShortVideoCategory).where(ShortVideoCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if category_in.name is not None:
        # 检查新名称是否与其他分类冲突
        existing = await db.execute(
            select(ShortVideoCategory).where(
                ShortVideoCategory.name == category_in.name,
                ShortVideoCategory.id != category_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"分类名称 '{category_in.name}' 已存在")
        category.name = category_in.name
    if category_in.description is not None:
        category.description = category_in.description
    if category_in.icon is not None:
        category.icon = category_in.icon
    if category_in.sort_order is not None:
        category.sort_order = category_in.sort_order
    if category_in.is_active is not None:
        category.is_active = category_in.is_active
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.delete("/short-categories/{category_id}")
async def delete_short_category(
    category_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除短视频分类"""
    result = await db.execute(select(ShortVideoCategory).where(ShortVideoCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 检查是否有视频使用此分类
    video_count_result = await db.execute(
        select(Video).where(Video.short_category_id == category_id).limit(1)
    )
    if video_count_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该分类下有短视频，无法删除。请先移动或删除相关视频。")
    
    # 硬删除
    await db.delete(category)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 标签管理 ==========

class TagCreate(BaseModel):
    name: str


class TagUpdate(BaseModel):
    name: Optional[str] = None


class TagResponse(BaseModel):
    id: int
    name: str
    use_count: int = 0
    
    class Config:
        from_attributes = True


@router.get("/tags", response_model=List[TagResponse])
async def get_all_tags(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取所有标签"""
    result = await db.execute(
        select(VideoTag).order_by(desc(VideoTag.use_count), VideoTag.id)
    )
    tags = result.scalars().all()
    
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            use_count=tag.use_count
        )
        for tag in tags
    ]


@router.post("/tags", response_model=TagResponse)
async def create_tag(
    tag_in: TagCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建标签"""
    # 检查是否已存在
    result = await db.execute(select(VideoTag).where(VideoTag.name == tag_in.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="标签已存在")
    
    tag = VideoTag(name=tag_in.name, use_count=0)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        use_count=tag.use_count
    )


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_in: TagUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新标签"""
    result = await db.execute(select(VideoTag).where(VideoTag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    if tag_in.name is not None:
        # 检查名称是否重复
        existing = await db.execute(
            select(VideoTag).where(VideoTag.name == tag_in.name, VideoTag.id != tag_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="标签名称已存在")
        tag.name = tag_in.name
    
    await db.commit()
    await db.refresh(tag)
    
    return TagResponse(
        id=tag.id,
        name=tag.name,
        use_count=tag.use_count
    )


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除标签"""
    result = await db.execute(select(VideoTag).where(VideoTag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    await db.delete(tag)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 评论管理 ==========

class CommentAdminResponse(BaseModel):
    id: int
    content: str
    image_url: Optional[str] = None
    video_id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    parent_id: Optional[int] = None
    like_count: int
    reply_count: int
    is_pinned: bool
    is_hidden: bool
    is_official: bool = False
    created_at: datetime

class CommentListAdminResponse(BaseModel):
    items: List[CommentAdminResponse]
    total: int
    page: int
    page_size: int

class CommentUpdateRequest(BaseModel):
    is_pinned: Optional[bool] = None
    is_hidden: Optional[bool] = None
    is_official: Optional[bool] = None

class BatchDeleteRequest(BaseModel):
    ids: List[int]


@router.get("/comments", response_model=CommentListAdminResponse)
async def list_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    video_id: Optional[int] = None,
    is_hidden: Optional[bool] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评论列表（管理员）"""
    query = select(Comment)
    count_query = select(func.count(Comment.id))
    
    # 搜索过滤
    if search:
        query = query.where(Comment.content.ilike(f"%{search}%"))
        count_query = count_query.where(Comment.content.ilike(f"%{search}%"))
    
    if video_id:
        query = query.where(Comment.video_id == video_id)
        count_query = count_query.where(Comment.video_id == video_id)
    
    if is_hidden is not None:
        query = query.where(Comment.is_hidden == is_hidden)
        count_query = count_query.where(Comment.is_hidden == is_hidden)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.order_by(desc(Comment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    items = []
    for comment in comments:
        # 获取用户信息
        user_result = await db.execute(select(User).where(User.id == comment.user_id))
        user = user_result.scalar_one_or_none()
        
        items.append(CommentAdminResponse(
            id=comment.id,
            content=comment.content,
            image_url=comment.image_url if hasattr(comment, 'image_url') else None,
            video_id=comment.video_id,
            user_id=comment.user_id,
            user_name=user.nickname or user.username if user else "未知用户",
            user_avatar=user.avatar if user else None,
            parent_id=comment.parent_id,
            like_count=comment.like_count,
            reply_count=comment.reply_count,
            is_pinned=comment.is_pinned,
            is_hidden=comment.is_hidden,
            is_official=comment.is_official if hasattr(comment, 'is_official') else False,
            created_at=comment.created_at
        ))
    
    return CommentListAdminResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: int,
    data: CommentUpdateRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新评论状态（管理员）"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    if data.is_pinned is not None:
        comment.is_pinned = data.is_pinned
    
    if data.is_hidden is not None:
        comment.is_hidden = data.is_hidden
    
    if data.is_official is not None:
        comment.is_official = data.is_official
    
    await db.commit()
    
    return {"message": "更新成功"}


@router.delete("/comments/{comment_id}")
async def delete_comment_admin(
    comment_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除评论（管理员）"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 如果是父评论，同时删除所有回复
    if comment.parent_id is None:
        await db.execute(
            select(Comment).where(Comment.parent_id == comment_id)
        )
        # 删除子评论
        from sqlalchemy import delete as sql_delete
        await db.execute(sql_delete(Comment).where(Comment.parent_id == comment_id))
    
    # 更新视频评论数
    video_result = await db.execute(select(Video).where(Video.id == comment.video_id))
    video = video_result.scalar_one_or_none()
    if video:
        video.comment_count = max(0, video.comment_count - 1 - comment.reply_count)
    
    await db.delete(comment)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/comments/batch-delete")
async def batch_delete_comments(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """批量删除评论（管理员）"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的评论")
    
    from sqlalchemy import delete as sql_delete
    
    # 先删除子评论
    await db.execute(sql_delete(Comment).where(Comment.parent_id.in_(data.ids)))
    
    # 再删除主评论
    await db.execute(sql_delete(Comment).where(Comment.id.in_(data.ids)))
    
    await db.commit()
    
    return {"message": f"成功删除 {len(data.ids)} 条评论"}


# ========== 代理管理 ==========

@router.get("/agents")
async def get_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    level: Optional[int] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取代理列表"""
    from app.models.promotion import UserProfile
    
    query = select(UserProfile, User).join(User, UserProfile.user_id == User.id)
    
    if status:
        query = query.where(UserProfile.agent_status == status)
    if level is not None:
        query = query.where(UserProfile.agent_level == level)
    
    # 只显示代理或待审核的用户
    query = query.where(
        (UserProfile.agent_level > 0) | (UserProfile.agent_status == "pending")
    )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(UserProfile.agent_applied_at)).offset(offset).limit(page_size)
    )
    
    agents = []
    for profile, user in result.all():
        agents.append({
            "id": profile.id,
            "user_id": user.id,
            "username": user.username,
            "agent_level": profile.agent_level,
            "agent_status": profile.agent_status,
            "commission_rate": float(profile.commission_rate),
            "total_invites": profile.total_invites,
            "valid_invites": profile.valid_invites,
            "total_commission": float(profile.total_commission),
            "available_balance": float(profile.available_balance),
            "agent_applied_at": profile.agent_applied_at,
            "agent_approved_at": profile.agent_approved_at
        })
    
    return {
        "items": agents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


class CreateAgentRequest(BaseModel):
    """创建代理请求"""
    # 新建账号
    username: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    # 或选择现有用户
    user_id: Optional[int] = None
    # 代理设置
    agent_level: int = 2
    commission_rate: Optional[float] = None
    parent_agent_id: Optional[int] = None
    remark: Optional[str] = None


@router.post("/agents/create")
async def create_agent(
    request: CreateAgentRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """手动创建代理账号"""
    from app.models.promotion import UserProfile
    from app.core.security import get_password_hash
    from decimal import Decimal
    import random
    import string
    
    user = None
    
    if request.user_id:
        # 从现有用户选择
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    elif request.username and request.password:
        # 新建账号
        # 检查用户名是否存在
        result = await db.execute(select(User).where(User.username == request.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 先创建用户（邀请码暂时为空）
        user = User(
            username=request.username,
            phone=request.phone,
            hashed_password=get_password_hash(request.password),
            role=UserRole.USER
        )
        db.add(user)
        await db.flush()
        
        # 基于用户ID生成唯一邀请码
        from app.core.invite_code import encode_user_id
        new_invite_code = encode_user_id(user.id)
        user.invite_code = new_invite_code
        
        # 创建VIP记录
        vip = UserVIP(user_id=user.id)
        db.add(vip)
        
        # 立即创建推广资料（使用相同的邀请码）
        profile = UserProfile(
            user_id=user.id,
            invite_code=new_invite_code,
            inviter_id=request.parent_agent_id
        )
        db.add(profile)
    else:
        raise HTTPException(status_code=400, detail="请提供用户ID或新建账号信息")
    
    # 如果是选择现有用户，需要检查/创建推广资料
    if request.user_id:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            # 基于用户ID生成唯一邀请码
            from app.core.invite_code import encode_user_id
            unique_code = encode_user_id(user.id)
            
            profile = UserProfile(
                user_id=user.id,
                invite_code=unique_code,
                inviter_id=request.parent_agent_id
            )
            db.add(profile)
    
    # 设置代理等级
    profile.agent_level = request.agent_level
    profile.agent_status = "active"
    profile.agent_approved_at = datetime.utcnow()
    
    # 设置佣金比例
    if request.commission_rate is not None:
        profile.commission_rate = Decimal(str(request.commission_rate / 100))
    else:
        # 从配置获取等级对应的佣金比例
        from app.models.system_config import SystemConfig
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{request.agent_level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认佣金比例
            rates = {1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(request.agent_level, Decimal("0.40"))
    
    await db.commit()
    
    return {
        "success": True,
        "message": "代理创建成功",
        "user_id": user.id,
        "username": user.username,
        "agent_level": profile.agent_level
    }


@router.get("/agents/search-users")
async def search_users_for_agent(
    keyword: str = Query(..., min_length=1),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索用户（用于选择现有用户设为代理）"""
    from app.models.promotion import UserProfile
    
    # 搜索用户
    result = await db.execute(
        select(User).where(
            (User.username.ilike(f"%{keyword}%")) |
            (User.phone.ilike(f"%{keyword}%"))
        ).limit(20)
    )
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        # 检查是否已是代理
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        user_list.append({
            "id": user.id,
            "username": user.username,
            "phone": user.phone,
            "is_agent": profile.agent_level > 0 if profile else False,
            "agent_level": profile.agent_level if profile else 0
        })
    
    return user_list


@router.post("/agents/{user_id}/approve")
async def approve_agent(
    user_id: int,
    level: int = Query(1, ge=1, le=6),
    commission_rate: Optional[float] = Query(None, ge=0.01, le=1.0),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """审批代理申请"""
    from app.models.promotion import UserProfile
    from app.models.system_config import SystemConfig
    from decimal import Decimal
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if profile.agent_status != "pending":
        raise HTTPException(status_code=400, detail="该用户没有待审核的申请")
    
    # 设置代理等级
    profile.agent_level = level
    profile.agent_status = "active"
    profile.agent_approved_at = datetime.utcnow()
    
    # 如果提供了自定义佣金比例，使用自定义的
    if commission_rate is not None:
        profile.commission_rate = Decimal(str(commission_rate))
    else:
        # 从配置获取等级对应的佣金比例
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认比例
            rates = {1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(level, Decimal("0.40"))
    
    await db.commit()
    
    return {"message": "审批通过", "agent_level": level}


@router.post("/agents/{user_id}/reject")
async def reject_agent(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """拒绝代理申请"""
    from app.models.promotion import UserProfile
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    profile.agent_status = "rejected"
    await db.commit()
    
    return {"message": "已拒绝"}


@router.post("/agents/{user_id}/update")
async def update_agent(
    user_id: int,
    level: int = Query(..., ge=0, le=6),
    status: str = Query(...),
    commission_rate: Optional[float] = Query(None, ge=0.01, le=1.0),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新代理信息"""
    from app.models.promotion import UserProfile
    from app.models.system_config import SystemConfig
    from decimal import Decimal
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    profile.agent_level = level
    profile.agent_status = status
    
    # 如果提供了自定义佣金比例，使用自定义的
    if commission_rate is not None:
        profile.commission_rate = Decimal(str(commission_rate))
    else:
        # 从配置获取等级对应的佣金比例
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认比例
            rates = {0: Decimal("0"), 1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(level, Decimal("0.40"))
    
    await db.commit()
    
    return {"message": "更新成功"}


# ========== 提现管理 ==========

@router.get("/withdrawals")
async def get_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提现列表"""
    from app.models.promotion import Withdrawal
    
    query = select(Withdrawal, User).join(User, Withdrawal.user_id == User.id)
    
    if status:
        query = query.where(Withdrawal.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(Withdrawal.created_at)).offset(offset).limit(page_size)
    )
    
    withdrawals = []
    for withdrawal, user in result.all():
        withdrawals.append({
            "id": withdrawal.id,
            "user_id": user.id,
            "username": user.username,
            "amount": float(withdrawal.amount),
            "fee": float(withdrawal.fee),
            "actual_amount": float(withdrawal.actual_amount),
            "withdraw_type": withdrawal.withdraw_type,
            "account_name": withdrawal.account_name,
            "account_number": withdrawal.account_number,
            "bank_name": withdrawal.bank_name,
            "status": withdrawal.status,
            "reject_reason": withdrawal.reject_reason,
            "created_at": withdrawal.created_at,
            "processed_at": withdrawal.processed_at
        })
    
    return {
        "items": withdrawals,
        "total": total,
        "page": page,
        "page_size": page_size
    }


class WithdrawProcessRequest(BaseModel):
    action: str  # approve/reject
    reject_reason: Optional[str] = None


@router.post("/withdrawals/{withdrawal_id}/process")
async def process_withdrawal(
    withdrawal_id: int,
    request: WithdrawProcessRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """处理提现申请"""
    from app.models.promotion import Withdrawal, UserProfile
    
    result = await db.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现记录不存在")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="该提现已处理")
    
    # 获取用户资料
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == withdrawal.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    if request.action == "approve":
        withdrawal.status = "success"
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.operator_id = current_user.id
        
        if profile:
            # 从冻结金额扣除
            profile.frozen_balance -= withdrawal.amount
            profile.total_withdrawn += withdrawal.actual_amount
        
        message = "提现已批准"
        
    elif request.action == "reject":
        withdrawal.status = "rejected"
        withdrawal.reject_reason = request.reject_reason
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.operator_id = current_user.id
        
        if profile:
            # 将冻结金额退回可用余额
            profile.frozen_balance -= withdrawal.amount
            profile.available_balance += withdrawal.amount
        
        message = "提现已拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    await db.commit()
    
    return {"message": message}


# ========== 推广统计 ==========

@router.get("/promotion/stats")
async def get_promotion_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取推广统计数据"""
    from app.models.promotion import UserProfile, Invitation, Commission, Withdrawal
    from sqlalchemy import and_
    
    # 今日开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总邀请数
    total_invites = (await db.execute(
        select(func.count(Invitation.id))
    )).scalar() or 0
    
    # 今日邀请数
    today_invites = (await db.execute(
        select(func.count(Invitation.id)).where(Invitation.created_at >= today_start)
    )).scalar() or 0
    
    # 有效邀请数
    valid_invites = (await db.execute(
        select(func.count(Invitation.id)).where(Invitation.is_valid == True)
    )).scalar() or 0
    
    # 总代理数
    total_agents = (await db.execute(
        select(func.count(UserProfile.id)).where(UserProfile.agent_level > 0)
    )).scalar() or 0
    
    # 待审核代理
    pending_agents = (await db.execute(
        select(func.count(UserProfile.id)).where(UserProfile.agent_status == "pending")
    )).scalar() or 0
    
    # 总佣金
    total_commission = (await db.execute(
        select(func.sum(Commission.commission_amount))
    )).scalar() or 0
    
    # 已提现
    total_withdrawn = (await db.execute(
        select(func.sum(Withdrawal.actual_amount)).where(Withdrawal.status == "success")
    )).scalar() or 0
    
    # 待处理提现
    pending_withdrawals = (await db.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == "pending")
    )).scalar() or 0
    
    return {
        "total_invites": total_invites,
        "today_invites": today_invites,
        "valid_invites": valid_invites,
        "total_agents": total_agents,
        "pending_agents": pending_agents,
        "total_commission": float(total_commission),
        "total_withdrawn": float(total_withdrawn),
        "pending_withdrawals": pending_withdrawals
    }


# ========== 里程碑配置 ==========

class MilestoneConfig(BaseModel):
    invite_count: int
    reward_type: str
    reward_value: float
    reward_desc: str


@router.get("/promotion/milestones")
async def get_milestones_config(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取里程碑配置"""
    from app.models.promotion import InviteMilestone
    
    result = await db.execute(
        select(InviteMilestone).order_by(InviteMilestone.invite_count)
    )
    milestones = result.scalars().all()
    
    return [{
        "id": m.id,
        "invite_count": m.invite_count,
        "reward_type": m.reward_type,
        "reward_value": float(m.reward_value),
        "reward_desc": m.reward_desc,
        "is_active": m.is_active
    } for m in milestones]


@router.post("/promotion/milestones")
async def create_milestone(
    config: MilestoneConfig,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建里程碑配置"""
    from app.models.promotion import InviteMilestone
    from decimal import Decimal
    
    milestone = InviteMilestone(
        invite_count=config.invite_count,
        reward_type=config.reward_type,
        reward_value=Decimal(str(config.reward_value)),
        reward_desc=config.reward_desc
    )
    db.add(milestone)
    await db.commit()
    
    return {"message": "创建成功", "id": milestone.id}


@router.delete("/promotion/milestones/{milestone_id}")
async def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除里程碑配置"""
    from app.models.promotion import InviteMilestone
    
    result = await db.execute(
        select(InviteMilestone).where(InviteMilestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    await db.delete(milestone)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 订单管理（配合代理系统） ==========

@router.get("/orders")
async def get_orders_with_commission(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表（含邀请人和佣金信息）"""
    from app.models.promotion import UserProfile, Commission
    
    query = select(PaymentOrder, User).join(User, PaymentOrder.user_id == User.id)
    
    if status:
        status_map = {
            'pending': PaymentStatus.PENDING,
            'success': PaymentStatus.SUCCESS,
            'failed': PaymentStatus.FAILED
        }
        if status in status_map:
            query = query.where(PaymentOrder.status == status_map[status])
    
    if start_date:
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.where(PaymentOrder.created_at >= start)
    
    if end_date:
        from datetime import datetime
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.where(PaymentOrder.created_at <= end)
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(PaymentOrder.created_at)).offset(offset).limit(page_size)
    )
    
    orders = []
    for order, user in result.all():
        # 获取用户的邀请人信息
        inviter_info = None
        commission_info = None
        
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        user_profile = profile_result.scalar_one_or_none()
        
        if user_profile and user_profile.inviter_id:
            # 获取邀请人信息
            inviter_result = await db.execute(
                select(User, UserProfile).join(
                    UserProfile, User.id == UserProfile.user_id
                ).where(User.id == user_profile.inviter_id)
            )
            inviter_row = inviter_result.first()
            if inviter_row:
                inviter, inviter_profile = inviter_row
                level_names = ['普通用户', '推广达人', '普通代理', '高级代理', '超级代理']
                inviter_info = {
                    'name': inviter.username,
                    'level': inviter_profile.agent_level,
                    'level_name': level_names[inviter_profile.agent_level] if inviter_profile.agent_level < len(level_names) else '普通用户'
                }
                
                # 获取该订单产生的佣金
                commission_result = await db.execute(
                    select(Commission).where(
                        Commission.order_id == order.id,
                        Commission.agent_id == user_profile.inviter_id
                    )
                )
                commission = commission_result.scalar_one_or_none()
                if commission:
                    commission_info = {
                        'amount': float(commission.commission_amount),
                        'rate': float(commission.commission_rate)
                    }
        
        orders.append({
            'id': order.id,
            'order_no': order.order_no,
            'user_id': user.id,
            'username': user.username,
            'order_type': order.order_type.value if hasattr(order.order_type, 'value') else order.order_type,
            'amount': float(order.amount),
            'status': order.status.value if hasattr(order.status, 'value') else order.status,
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'paid_at': order.paid_at.isoformat() if order.paid_at else None,
            'inviter_name': inviter_info['name'] if inviter_info else None,
            'inviter_level_name': inviter_info['level_name'] if inviter_info else None,
            'commission_amount': commission_info['amount'] if commission_info else 0,
            'commission_rate': commission_info['rate'] if commission_info else 0
        })
    
    return {
        'items': orders,
        'total': total,
        'page': page,
        'page_size': page_size
    }


@router.get("/orders/stats")
async def get_orders_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单统计"""
    from app.models.promotion import Commission
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总订单数
    total_orders = (await db.execute(
        select(func.count(PaymentOrder.id))
    )).scalar() or 0
    
    # 总金额（已支付）
    total_amount = (await db.execute(
        select(func.sum(PaymentOrder.amount)).where(PaymentOrder.status == PaymentStatus.SUCCESS)
    )).scalar() or 0
    
    # 今日订单
    today_orders = (await db.execute(
        select(func.count(PaymentOrder.id)).where(PaymentOrder.created_at >= today_start)
    )).scalar() or 0
    
    # 产生的总佣金
    total_commission = (await db.execute(
        select(func.sum(Commission.commission_amount))
    )).scalar() or 0
    
    return {
        'total_orders': total_orders,
        'total_amount': float(total_amount),
        'today_orders': today_orders,
        'total_commission': float(total_commission)
    }

    query = query.where(
        (UserProfile.agent_level > 0) | (UserProfile.agent_status == "pending")
    )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(UserProfile.agent_applied_at)).offset(offset).limit(page_size)
    )
    
    agents = []
    for profile, user in result.all():
        agents.append({
            "id": profile.id,
            "user_id": user.id,
            "username": user.username,
            "agent_level": profile.agent_level,
            "agent_status": profile.agent_status,
            "commission_rate": float(profile.commission_rate),
            "total_invites": profile.total_invites,
            "valid_invites": profile.valid_invites,
            "total_commission": float(profile.total_commission),
            "available_balance": float(profile.available_balance),
            "agent_applied_at": profile.agent_applied_at,
            "agent_approved_at": profile.agent_approved_at
        })
    
    return {
        "items": agents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


class CreateAgentRequest(BaseModel):
    """创建代理请求"""
    # 新建账号
    username: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    # 或选择现有用户
    user_id: Optional[int] = None
    # 代理设置
    agent_level: int = 2
    commission_rate: Optional[float] = None
    parent_agent_id: Optional[int] = None
    remark: Optional[str] = None


@router.post("/agents/create")
async def create_agent(
    request: CreateAgentRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """手动创建代理账号"""
    from app.models.promotion import UserProfile
    from app.core.security import get_password_hash
    from decimal import Decimal
    import random
    import string
    
    user = None
    
    if request.user_id:
        # 从现有用户选择
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
    elif request.username and request.password:
        # 新建账号
        # 检查用户名是否存在
        result = await db.execute(select(User).where(User.username == request.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 先创建用户（邀请码暂时为空）
        user = User(
            username=request.username,
            phone=request.phone,
            hashed_password=get_password_hash(request.password),
            role=UserRole.USER
        )
        db.add(user)
        await db.flush()
        
        # 基于用户ID生成唯一邀请码
        from app.core.invite_code import encode_user_id
        new_invite_code = encode_user_id(user.id)
        user.invite_code = new_invite_code
        
        # 创建VIP记录
        vip = UserVIP(user_id=user.id)
        db.add(vip)
        
        # 立即创建推广资料（使用相同的邀请码）
        profile = UserProfile(
            user_id=user.id,
            invite_code=new_invite_code,
            inviter_id=request.parent_agent_id
        )
        db.add(profile)
    else:
        raise HTTPException(status_code=400, detail="请提供用户ID或新建账号信息")
    
    # 如果是选择现有用户，需要检查/创建推广资料
    if request.user_id:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            # 基于用户ID生成唯一邀请码
            from app.core.invite_code import encode_user_id
            unique_code = encode_user_id(user.id)
            
            profile = UserProfile(
                user_id=user.id,
                invite_code=unique_code,
                inviter_id=request.parent_agent_id
            )
            db.add(profile)
    
    # 设置代理等级
    profile.agent_level = request.agent_level
    profile.agent_status = "active"
    profile.agent_approved_at = datetime.utcnow()
    
    # 设置佣金比例
    if request.commission_rate is not None:
        profile.commission_rate = Decimal(str(request.commission_rate / 100))
    else:
        # 从配置获取等级对应的佣金比例
        from app.models.system_config import SystemConfig
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{request.agent_level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认佣金比例
            rates = {1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(request.agent_level, Decimal("0.40"))
    
    await db.commit()
    
    return {
        "success": True,
        "message": "代理创建成功",
        "user_id": user.id,
        "username": user.username,
        "agent_level": profile.agent_level
    }


@router.get("/agents/search-users")
async def search_users_for_agent(
    keyword: str = Query(..., min_length=1),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索用户（用于选择现有用户设为代理）"""
    from app.models.promotion import UserProfile
    
    # 搜索用户
    result = await db.execute(
        select(User).where(
            (User.username.ilike(f"%{keyword}%")) |
            (User.phone.ilike(f"%{keyword}%"))
        ).limit(20)
    )
    users = result.scalars().all()
    
    user_list = []
    for user in users:
        # 检查是否已是代理
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        user_list.append({
            "id": user.id,
            "username": user.username,
            "phone": user.phone,
            "is_agent": profile.agent_level > 0 if profile else False,
            "agent_level": profile.agent_level if profile else 0
        })
    
    return user_list


@router.post("/agents/{user_id}/approve")
async def approve_agent(
    user_id: int,
    level: int = Query(1, ge=1, le=6),
    commission_rate: Optional[float] = Query(None, ge=0.01, le=1.0),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """审批代理申请"""
    from app.models.promotion import UserProfile
    from app.models.system_config import SystemConfig
    from decimal import Decimal
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if profile.agent_status != "pending":
        raise HTTPException(status_code=400, detail="该用户没有待审核的申请")
    
    # 设置代理等级
    profile.agent_level = level
    profile.agent_status = "active"
    profile.agent_approved_at = datetime.utcnow()
    
    # 如果提供了自定义佣金比例，使用自定义的
    if commission_rate is not None:
        profile.commission_rate = Decimal(str(commission_rate))
    else:
        # 从配置获取等级对应的佣金比例
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认比例
            rates = {1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(level, Decimal("0.40"))
    
    await db.commit()
    
    return {"message": "审批通过", "agent_level": level}


@router.post("/agents/{user_id}/reject")
async def reject_agent(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """拒绝代理申请"""
    from app.models.promotion import UserProfile
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    profile.agent_status = "rejected"
    await db.commit()
    
    return {"message": "已拒绝"}


@router.post("/agents/{user_id}/update")
async def update_agent(
    user_id: int,
    level: int = Query(..., ge=0, le=6),
    status: str = Query(...),
    commission_rate: Optional[float] = Query(None, ge=0.01, le=1.0),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """更新代理信息"""
    from app.models.promotion import UserProfile
    from app.models.system_config import SystemConfig
    from decimal import Decimal
    
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    profile.agent_level = level
    profile.agent_status = status
    
    # 如果提供了自定义佣金比例，使用自定义的
    if commission_rate is not None:
        profile.commission_rate = Decimal(str(commission_rate))
    else:
        # 从配置获取等级对应的佣金比例
        config_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == f"agent_level_{level}_rate")
        )
        config = config_result.scalar_one_or_none()
        if config:
            profile.commission_rate = Decimal(str(int(config.value) / 100))
        else:
            # 默认比例
            rates = {0: Decimal("0"), 1: Decimal("0.40"), 2: Decimal("0.46"), 3: Decimal("0.52"), 4: Decimal("0.58"), 5: Decimal("0.64"), 6: Decimal("0.70")}
            profile.commission_rate = rates.get(level, Decimal("0.40"))
    
    await db.commit()
    
    return {"message": "更新成功"}


# ========== 提现管理 ==========

@router.get("/withdrawals")
async def get_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提现列表"""
    from app.models.promotion import Withdrawal
    
    query = select(Withdrawal, User).join(User, Withdrawal.user_id == User.id)
    
    if status:
        query = query.where(Withdrawal.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(Withdrawal.created_at)).offset(offset).limit(page_size)
    )
    
    withdrawals = []
    for withdrawal, user in result.all():
        withdrawals.append({
            "id": withdrawal.id,
            "user_id": user.id,
            "username": user.username,
            "amount": float(withdrawal.amount),
            "fee": float(withdrawal.fee),
            "actual_amount": float(withdrawal.actual_amount),
            "withdraw_type": withdrawal.withdraw_type,
            "account_name": withdrawal.account_name,
            "account_number": withdrawal.account_number,
            "bank_name": withdrawal.bank_name,
            "status": withdrawal.status,
            "reject_reason": withdrawal.reject_reason,
            "created_at": withdrawal.created_at,
            "processed_at": withdrawal.processed_at
        })
    
    return {
        "items": withdrawals,
        "total": total,
        "page": page,
        "page_size": page_size
    }


class WithdrawProcessRequest(BaseModel):
    action: str  # approve/reject
    reject_reason: Optional[str] = None


@router.post("/withdrawals/{withdrawal_id}/process")
async def process_withdrawal(
    withdrawal_id: int,
    request: WithdrawProcessRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """处理提现申请"""
    from app.models.promotion import Withdrawal, UserProfile
    
    result = await db.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="提现记录不存在")
    
    if withdrawal.status != "pending":
        raise HTTPException(status_code=400, detail="该提现已处理")
    
    # 获取用户资料
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == withdrawal.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    if request.action == "approve":
        withdrawal.status = "success"
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.operator_id = current_user.id
        
        if profile:
            # 从冻结金额扣除
            profile.frozen_balance -= withdrawal.amount
            profile.total_withdrawn += withdrawal.actual_amount
        
        message = "提现已批准"
        
    elif request.action == "reject":
        withdrawal.status = "rejected"
        withdrawal.reject_reason = request.reject_reason
        withdrawal.processed_at = datetime.utcnow()
        withdrawal.operator_id = current_user.id
        
        if profile:
            # 将冻结金额退回可用余额
            profile.frozen_balance -= withdrawal.amount
            profile.available_balance += withdrawal.amount
        
        message = "提现已拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    await db.commit()
    
    return {"message": message}


# ========== 推广统计 ==========

@router.get("/promotion/stats")
async def get_promotion_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取推广统计数据"""
    from app.models.promotion import UserProfile, Invitation, Commission, Withdrawal
    from sqlalchemy import and_
    
    # 今日开始时间
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总邀请数
    total_invites = (await db.execute(
        select(func.count(Invitation.id))
    )).scalar() or 0
    
    # 今日邀请数
    today_invites = (await db.execute(
        select(func.count(Invitation.id)).where(Invitation.created_at >= today_start)
    )).scalar() or 0
    
    # 有效邀请数
    valid_invites = (await db.execute(
        select(func.count(Invitation.id)).where(Invitation.is_valid == True)
    )).scalar() or 0
    
    # 总代理数
    total_agents = (await db.execute(
        select(func.count(UserProfile.id)).where(UserProfile.agent_level > 0)
    )).scalar() or 0
    
    # 待审核代理
    pending_agents = (await db.execute(
        select(func.count(UserProfile.id)).where(UserProfile.agent_status == "pending")
    )).scalar() or 0
    
    # 总佣金
    total_commission = (await db.execute(
        select(func.sum(Commission.commission_amount))
    )).scalar() or 0
    
    # 已提现
    total_withdrawn = (await db.execute(
        select(func.sum(Withdrawal.actual_amount)).where(Withdrawal.status == "success")
    )).scalar() or 0
    
    # 待处理提现
    pending_withdrawals = (await db.execute(
        select(func.count(Withdrawal.id)).where(Withdrawal.status == "pending")
    )).scalar() or 0
    
    return {
        "total_invites": total_invites,
        "today_invites": today_invites,
        "valid_invites": valid_invites,
        "total_agents": total_agents,
        "pending_agents": pending_agents,
        "total_commission": float(total_commission),
        "total_withdrawn": float(total_withdrawn),
        "pending_withdrawals": pending_withdrawals
    }


# ========== 里程碑配置 ==========

class MilestoneConfig(BaseModel):
    invite_count: int
    reward_type: str
    reward_value: float
    reward_desc: str


@router.get("/promotion/milestones")
async def get_milestones_config(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取里程碑配置"""
    from app.models.promotion import InviteMilestone
    
    result = await db.execute(
        select(InviteMilestone).order_by(InviteMilestone.invite_count)
    )
    milestones = result.scalars().all()
    
    return [{
        "id": m.id,
        "invite_count": m.invite_count,
        "reward_type": m.reward_type,
        "reward_value": float(m.reward_value),
        "reward_desc": m.reward_desc,
        "is_active": m.is_active
    } for m in milestones]


@router.post("/promotion/milestones")
async def create_milestone(
    config: MilestoneConfig,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """创建里程碑配置"""
    from app.models.promotion import InviteMilestone
    from decimal import Decimal
    
    milestone = InviteMilestone(
        invite_count=config.invite_count,
        reward_type=config.reward_type,
        reward_value=Decimal(str(config.reward_value)),
        reward_desc=config.reward_desc
    )
    db.add(milestone)
    await db.commit()
    
    return {"message": "创建成功", "id": milestone.id}


@router.delete("/promotion/milestones/{milestone_id}")
async def delete_milestone(
    milestone_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """删除里程碑配置"""
    from app.models.promotion import InviteMilestone
    
    result = await db.execute(
        select(InviteMilestone).where(InviteMilestone.id == milestone_id)
    )
    milestone = result.scalar_one_or_none()
    
    if not milestone:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    await db.delete(milestone)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 订单管理（配合代理系统） ==========

@router.get("/orders")
async def get_orders_with_commission(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单列表（含邀请人和佣金信息）"""
    from app.models.promotion import UserProfile, Commission
    
    query = select(PaymentOrder, User).join(User, PaymentOrder.user_id == User.id)
    
    if status:
        status_map = {
            'pending': PaymentStatus.PENDING,
            'success': PaymentStatus.SUCCESS,
            'failed': PaymentStatus.FAILED
        }
        if status in status_map:
            query = query.where(PaymentOrder.status == status_map[status])
    
    if start_date:
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.where(PaymentOrder.created_at >= start)
    
    if end_date:
        from datetime import datetime
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        query = query.where(PaymentOrder.created_at <= end)
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(PaymentOrder.created_at)).offset(offset).limit(page_size)
    )
    
    orders = []
    for order, user in result.all():
        # 获取用户的邀请人信息
        inviter_info = None
        commission_info = None
        
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        user_profile = profile_result.scalar_one_or_none()
        
        if user_profile and user_profile.inviter_id:
            # 获取邀请人信息
            inviter_result = await db.execute(
                select(User, UserProfile).join(
                    UserProfile, User.id == UserProfile.user_id
                ).where(User.id == user_profile.inviter_id)
            )
            inviter_row = inviter_result.first()
            if inviter_row:
                inviter, inviter_profile = inviter_row
                level_names = ['普通用户', '推广达人', '普通代理', '高级代理', '超级代理']
                inviter_info = {
                    'name': inviter.username,
                    'level': inviter_profile.agent_level,
                    'level_name': level_names[inviter_profile.agent_level] if inviter_profile.agent_level < len(level_names) else '普通用户'
                }
                
                # 获取该订单产生的佣金
                commission_result = await db.execute(
                    select(Commission).where(
                        Commission.order_id == order.id,
                        Commission.agent_id == user_profile.inviter_id
                    )
                )
                commission = commission_result.scalar_one_or_none()
                if commission:
                    commission_info = {
                        'amount': float(commission.commission_amount),
                        'rate': float(commission.commission_rate)
                    }
        
        orders.append({
            'id': order.id,
            'order_no': order.order_no,
            'user_id': user.id,
            'username': user.username,
            'order_type': order.order_type.value if hasattr(order.order_type, 'value') else order.order_type,
            'amount': float(order.amount),
            'status': order.status.value if hasattr(order.status, 'value') else order.status,
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'paid_at': order.paid_at.isoformat() if order.paid_at else None,
            'inviter_name': inviter_info['name'] if inviter_info else None,
            'inviter_level_name': inviter_info['level_name'] if inviter_info else None,
            'commission_amount': commission_info['amount'] if commission_info else 0,
            'commission_rate': commission_info['rate'] if commission_info else 0
        })
    
    return {
        'items': orders,
        'total': total,
        'page': page,
        'page_size': page_size
    }


@router.get("/orders/stats")
async def get_orders_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订单统计"""
    from app.models.promotion import Commission
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总订单数
    total_orders = (await db.execute(
        select(func.count(PaymentOrder.id))
    )).scalar() or 0
    
    # 总金额（已支付）
    total_amount = (await db.execute(
        select(func.sum(PaymentOrder.amount)).where(PaymentOrder.status == PaymentStatus.SUCCESS)
    )).scalar() or 0
    
    # 今日订单
    today_orders = (await db.execute(
        select(func.count(PaymentOrder.id)).where(PaymentOrder.created_at >= today_start)
    )).scalar() or 0
    
    # 产生的总佣金
    total_commission = (await db.execute(
        select(func.sum(Commission.commission_amount))
    )).scalar() or 0
    
    return {
        'total_orders': total_orders,
        'total_amount': float(total_amount),
        'today_orders': today_orders,
        'total_commission': float(total_commission)
    }