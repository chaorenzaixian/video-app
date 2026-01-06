"""
创作者系统API接口
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.video import Video
from app.models.creator import (
    CreatorApplication, Creator, CreatorEarning, CreatorWithdrawal,
    VideoTip, Gift, VideoReview, VideoCollection, CollectionVideo,
    UserFollow, TipRanking
)
from app.models.coins import UserCoins, CoinTransaction
from app.models.user import UserVIP

router = APIRouter(prefix="/creator", tags=["创作者系统"])


# ==================== VIP用户自动成为创作者 ====================

async def check_user_is_vip(user_id: int, db: AsyncSession) -> bool:
    """检查用户是否是VIP"""
    result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id == user_id,
            UserVIP.is_active == True,
            UserVIP.expire_date > datetime.utcnow()
        )
    )
    return result.scalar_one_or_none() is not None


async def ensure_vip_creator(user: User, db: AsyncSession) -> Creator:
    """
    确保VIP用户是创作者，如果不是则自动创建
    返回Creator对象，如果用户不是VIP也不是创作者则返回None
    """
    # 先检查是否已是创作者
    result = await db.execute(
        select(Creator).where(Creator.user_id == user.id)
    )
    creator = result.scalar_one_or_none()
    
    if creator:
        return creator
    
    # 检查是否是VIP
    is_vip = await check_user_is_vip(user.id, db)
    
    if not is_vip:
        return None
    
    # VIP用户自动创建创作者身份
    creator = Creator(
        user_id=user.id,
        display_name=user.nickname or user.username,
        avatar=user.avatar,
        bio=user.bio,
        creator_level=1,
        is_verified=False,
        is_active=True
    )
    db.add(creator)
    await db.commit()
    await db.refresh(creator)
    
    return creator


# ==================== Schemas ====================

class CreatorApplicationRequest(BaseModel):
    real_name: str
    phone: str
    email: Optional[str] = None
    introduction: str
    expertise: Optional[str] = None


class CreatorProfileResponse(BaseModel):
    id: int
    user_id: int
    display_name: Optional[str]
    avatar: Optional[str]
    bio: Optional[str]
    creator_level: int
    is_verified: bool
    verification_type: Optional[str]
    total_videos: int
    total_views: int
    total_followers: int
    total_coins_earned: int

    class Config:
        from_attributes = True


class VideoUploadRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    short_category_id: Optional[int] = None  # 短视频分类
    tags: Optional[List[str]] = None
    pay_type: str = "free"  # free/coins/vip_free
    coin_price: int = 0
    vip_free_level: int = 0
    # 短视频支持
    original_url: Optional[str] = None
    cover_url: Optional[str] = None
    duration: Optional[float] = None
    is_short: bool = False
    is_vip_only: bool = False


class TipRequest(BaseModel):
    coins_amount: int
    gift_id: Optional[int] = None
    message: Optional[str] = None
    is_anonymous: bool = False


class WithdrawalRequest(BaseModel):
    coins_amount: int
    payment_method: str  # alipay/wechat/bank
    payment_account: str
    payment_name: str


class CollectionCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    pay_type: str = "free"
    collection_price: int = 0
    single_video_price: int = 0


# ==================== 创作者申请 ====================

@router.post("/apply")
async def apply_creator(
    data: CreatorApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """申请成为创作者"""
    # 检查是否已经是创作者
    existing_creator = await db.execute(
        select(Creator).where(Creator.user_id == current_user.id)
    )
    if existing_creator.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已经是创作者")
    
    # 检查是否有待审核的申请
    pending_app = await db.execute(
        select(CreatorApplication).where(
            CreatorApplication.user_id == current_user.id,
            CreatorApplication.status == "pending"
        )
    )
    if pending_app.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您有待审核的申请")
    
    # 创建申请
    application = CreatorApplication(
        user_id=current_user.id,
        real_name=data.real_name,
        phone=data.phone,
        email=data.email,
        introduction=data.introduction,
        expertise=data.expertise
    )
    db.add(application)
    await db.commit()
    
    return {"message": "申请已提交，请等待审核", "application_id": application.id}


@router.get("/application/status")
async def get_application_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取创作者申请状态（VIP用户自动成为创作者）"""
    # VIP用户自动成为创作者
    creator = await ensure_vip_creator(current_user, db)
    
    if creator:
        return {
            "is_creator": True,
            "creator_id": creator.id,
            "creator_level": creator.creator_level,
            "is_verified": creator.is_verified,
            "is_vip_auto": True  # 标记是否为VIP自动创建
        }
    
    # 获取最新申请（非VIP用户需要申请）
    app_result = await db.execute(
        select(CreatorApplication)
        .where(CreatorApplication.user_id == current_user.id)
        .order_by(CreatorApplication.created_at.desc())
    )
    application = app_result.scalar_one_or_none()
    
    # 检查是否是VIP
    is_vip = await check_user_is_vip(current_user.id, db)
    
    if not application:
        return {
            "is_creator": False, 
            "has_application": False,
            "is_vip": is_vip,
            "message": "VIP用户可直接成为创作者" if is_vip else "请先开通VIP成为创作者"
        }
    
    return {
        "is_creator": False,
        "has_application": True,
        "application_status": application.status,
        "reject_reason": application.reject_reason if application.status == "rejected" else None,
        "submitted_at": application.created_at,
        "is_vip": is_vip
    }


# ==================== 创作者信息 ====================

@router.get("/profile", response_model=CreatorProfileResponse)
async def get_creator_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取创作者个人资料（VIP用户自动成为创作者）"""
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=404, detail="您还不是创作者，请先开通VIP")
    
    return creator


@router.put("/profile")
async def update_creator_profile(
    display_name: Optional[str] = None,
    bio: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新创作者资料（VIP用户自动成为创作者）"""
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=404, detail="您还不是创作者，请先开通VIP")
    
    if display_name:
        creator.display_name = display_name
    if bio is not None:
        creator.bio = bio
    if tags is not None:
        creator.tags = tags
    
    await db.commit()
    return {"message": "资料更新成功"}


@router.get("/dashboard")
async def get_creator_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取创作者数据面板（VIP用户自动成为创作者）"""
    # VIP用户自动成为创作者
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=404, detail="您还不是创作者，请先开通VIP")
    
    # 获取今日数据
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 今日收益
    today_earnings = await db.execute(
        select(func.sum(CreatorEarning.net_amount)).where(
            CreatorEarning.creator_id == creator.id,
            CreatorEarning.created_at >= today
        )
    )
    today_income = today_earnings.scalar() or 0
    
    # 今日打赏
    today_tips = await db.execute(
        select(func.sum(VideoTip.creator_income)).where(
            VideoTip.creator_id == creator.id,
            VideoTip.created_at >= today
        )
    )
    today_tip_income = today_tips.scalar() or 0
    
    # 待审核视频数
    pending_reviews = await db.execute(
        select(func.count(VideoReview.id)).where(
            VideoReview.status == "pending"
        ).join(Video).where(Video.uploader_id == current_user.id)
    )
    pending_count = pending_reviews.scalar() or 0
    
    return {
        "creator_level": creator.creator_level,
        "is_verified": creator.is_verified,
        "total_videos": creator.total_videos,
        "total_views": creator.total_views,
        "total_followers": creator.total_followers,
        "total_coins_earned": creator.total_coins_earned,
        "available_coins": creator.available_coins,
        "frozen_coins": creator.frozen_coins,
        "today_income": today_income,
        "today_tips": today_tip_income,
        "pending_reviews": pending_count,
        "platform_share_ratio": creator.platform_share_ratio
    }


# ==================== 视频上传与审核 ====================

@router.post("/videos/upload")
async def upload_video(
    data: VideoUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传视频(提交审核) - VIP用户自动成为创作者"""
    # VIP用户自动成为创作者
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=403, detail="只有VIP用户可以上传视频，请先开通VIP")
    
    if creator.is_banned:
        raise HTTPException(status_code=403, detail="您的创作者账号已被封禁")
    
    # 创建视频记录
    video = Video(
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        short_category_id=data.short_category_id,  # 短视频分类
        uploader_id=current_user.id,
        creator_id=creator.id,
        pay_type=data.pay_type,
        coin_price=data.coin_price,
        vip_free_level=data.vip_free_level,
        original_url=data.original_url,
        cover_url=data.cover_url,
        duration=data.duration,
        is_short=data.is_short,
        is_vip_only=data.is_vip_only,
        status="pending"  # 待审核状态
    )
    db.add(video)
    await db.flush()
    
    # 创建审核记录
    review = VideoReview(
        video_id=video.id,
        status="pending"
    )
    db.add(review)
    
    await db.commit()
    
    return {
        "message": "视频已提交审核",
        "video_id": video.id,
        "status": "pending"
    }


@router.get("/videos")
async def get_creator_videos(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取创作者的视频列表"""
    query = select(Video, VideoReview).outerjoin(
        VideoReview, Video.id == VideoReview.video_id
    ).where(Video.uploader_id == current_user.id)
    
    if status:
        query = query.where(VideoReview.status == status)
    
    query = query.order_by(Video.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    
    videos = []
    for video, review in result.all():
        videos.append({
            "id": video.id,
            "title": video.title,
            "cover_url": video.cover_url,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "pay_type": video.pay_type,
            "coin_price": video.coin_price,
            "review_status": review.status if review else None,
            "reject_reason": review.reject_reasons if review else None,
            "created_at": video.created_at
        })
    
    return videos


# ==================== 打赏系统 ====================

@router.post("/videos/{video_id}/tip")
async def tip_video(
    video_id: int,
    data: TipRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """打赏视频"""
    if data.coins_amount <= 0:
        raise HTTPException(status_code=400, detail="打赏金额必须大于0")
    
    # 获取视频
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 不能打赏自己
    if video.uploader_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能打赏自己的视频")
    
    # 获取创作者
    creator_result = await db.execute(
        select(Creator).where(Creator.user_id == video.uploader_id)
    )
    creator = creator_result.scalar_one_or_none()
    if not creator:
        raise HTTPException(status_code=400, detail="该视频上传者不是创作者")
    
    # 检查用户金币余额
    coins_result = await db.execute(
        select(UserCoins).where(UserCoins.user_id == current_user.id)
    )
    user_coins = coins_result.scalar_one_or_none()
    if not user_coins or user_coins.balance < data.coins_amount:
        raise HTTPException(status_code=400, detail="金币余额不足")
    
    # 计算分成
    platform_fee = int(data.coins_amount * creator.platform_share_ratio)
    creator_income = data.coins_amount - platform_fee
    
    # 扣除用户金币
    user_coins.balance -= data.coins_amount
    user_coins.total_spent += data.coins_amount
    
    # 记录用户金币变动
    coin_transaction = CoinTransaction(
        user_id=current_user.id,
        amount=-data.coins_amount,
        balance_after=user_coins.balance,
        transaction_type="tip",
        source_type="video",
        source_id=video_id,
        description=f"打赏视频: {video.title[:20]}"
    )
    db.add(coin_transaction)
    
    # 创建打赏记录
    tip = VideoTip(
        video_id=video_id,
        user_id=current_user.id,
        creator_id=creator.id,
        coins_amount=data.coins_amount,
        gift_id=data.gift_id,
        message=data.message,
        platform_fee=platform_fee,
        creator_income=creator_income,
        is_anonymous=data.is_anonymous
    )
    db.add(tip)
    
    # 增加创作者收益
    creator.total_tips_received += data.coins_amount
    creator.available_coins += creator_income
    creator.total_coins_earned += creator_income
    
    # 创建创作者收益记录
    earning = CreatorEarning(
        creator_id=creator.id,
        earning_type="tip",
        source_type="video",
        source_id=video_id,
        gross_amount=data.coins_amount,
        platform_fee=platform_fee,
        net_amount=creator_income,
        from_user_id=current_user.id,
        status="settled",
        settled_at=datetime.utcnow(),
        description=f"收到打赏 - {video.title[:20]}"
    )
    db.add(earning)
    
    await db.commit()
    
    return {
        "message": "打赏成功",
        "coins_amount": data.coins_amount,
        "creator_received": creator_income
    }


@router.get("/gifts")
async def get_gifts(db: AsyncSession = Depends(get_db)):
    """获取礼物列表"""
    result = await db.execute(
        select(Gift).where(Gift.is_active == True).order_by(Gift.sort_order)
    )
    gifts = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "name": g.name,
            "icon": g.icon,
            "animation_url": g.animation_url,
            "coins_price": g.coins_price
        }
        for g in gifts
    ]


# ==================== 打赏排行榜 ====================

@router.get("/rankings/tips")
async def get_tip_rankings(
    ranking_type: str = Query("weekly", regex="^(weekly|monthly|total)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取打赏排行榜"""
    # 计算时间范围
    now = datetime.utcnow()
    if ranking_type == "weekly":
        start_time = now - timedelta(days=7)
    elif ranking_type == "monthly":
        start_time = now - timedelta(days=30)
    else:
        start_time = None
    
    # 查询排行
    query = select(
        Creator.id,
        Creator.display_name,
        Creator.avatar,
        Creator.is_verified,
        func.sum(VideoTip.coins_amount).label("total_tips"),
        func.count(VideoTip.id).label("tip_count")
    ).join(VideoTip, Creator.id == VideoTip.creator_id)
    
    if start_time:
        query = query.where(VideoTip.created_at >= start_time)
    
    query = query.group_by(Creator.id).order_by(desc("total_tips")).limit(limit)
    
    result = await db.execute(query)
    
    rankings = []
    for idx, row in enumerate(result.all(), 1):
        rankings.append({
            "rank": idx,
            "creator_id": row.id,
            "display_name": row.display_name,
            "avatar": row.avatar,
            "is_verified": row.is_verified,
            "total_tips": row.total_tips or 0,
            "tip_count": row.tip_count or 0
        })
    
    return rankings


# ==================== 提现 ====================

@router.post("/withdraw")
async def create_withdrawal(
    data: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """申请提现（VIP用户自动成为创作者）"""
    # VIP用户自动成为创作者
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=404, detail="您还不是创作者，请先开通VIP")
    
    # 检查可提现金额
    if creator.available_coins < data.coins_amount:
        raise HTTPException(status_code=400, detail="可提现金币不足")
    
    # 最低提现额度
    min_withdraw = 1000  # 最低1000金币
    if data.coins_amount < min_withdraw:
        raise HTTPException(status_code=400, detail=f"最低提现{min_withdraw}金币")
    
    # 计算现金金额 (1金币 = 0.01元)
    exchange_rate = 0.01
    cash_amount = data.coins_amount * exchange_rate
    
    # 冻结金币
    creator.available_coins -= data.coins_amount
    creator.frozen_coins += data.coins_amount
    
    # 创建提现记录
    withdrawal = CreatorWithdrawal(
        creator_id=creator.id,
        coins_amount=data.coins_amount,
        cash_amount=cash_amount,
        exchange_rate=exchange_rate,
        payment_method=data.payment_method,
        payment_account=data.payment_account,
        payment_name=data.payment_name
    )
    db.add(withdrawal)
    
    await db.commit()
    
    return {
        "message": "提现申请已提交",
        "withdrawal_id": withdrawal.id,
        "coins_amount": data.coins_amount,
        "cash_amount": float(cash_amount)
    }


@router.get("/withdrawals")
async def get_withdrawals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提现记录（VIP用户自动成为创作者）"""
    # VIP用户自动成为创作者
    creator = await ensure_vip_creator(current_user, db)
    
    if not creator:
        raise HTTPException(status_code=404, detail="您还不是创作者，请先开通VIP")
    
    query = select(CreatorWithdrawal).where(
        CreatorWithdrawal.creator_id == creator.id
    ).order_by(CreatorWithdrawal.created_at.desc())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    
    return [
        {
            "id": w.id,
            "coins_amount": w.coins_amount,
            "cash_amount": float(w.cash_amount),
            "payment_method": w.payment_method,
            "status": w.status,
            "reject_reason": w.reject_reason,
            "created_at": w.created_at
        }
        for w in result.scalars().all()
    ]


# ==================== 关注系统 ====================

@router.post("/follow/{creator_id}")
async def follow_creator(
    creator_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """关注创作者"""
    # 获取创作者
    creator_result = await db.execute(
        select(Creator).where(Creator.id == creator_id)
    )
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(status_code=404, detail="创作者不存在")
    
    if creator.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    
    # 检查是否已关注
    existing = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == creator.user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已经关注了")
    
    # 创建关注
    follow = UserFollow(
        follower_id=current_user.id,
        following_id=creator.user_id
    )
    db.add(follow)
    
    # 更新创作者粉丝数
    creator.total_followers += 1
    
    await db.commit()
    
    return {"message": "关注成功"}


@router.delete("/follow/{creator_id}")
async def unfollow_creator(
    creator_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消关注"""
    creator_result = await db.execute(
        select(Creator).where(Creator.id == creator_id)
    )
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(status_code=404, detail="创作者不存在")
    
    # 查找关注记录
    follow_result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == creator.user_id
        )
    )
    follow = follow_result.scalar_one_or_none()
    
    if not follow:
        raise HTTPException(status_code=400, detail="未关注该创作者")
    
    await db.delete(follow)
    creator.total_followers = max(0, creator.total_followers - 1)
    
    await db.commit()
    
    return {"message": "已取消关注"}


@router.get("/following")
async def get_following_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取关注列表"""
    from datetime import datetime
    
    # 查询当前用户关注的人
    query = select(User, UserFollow).join(
        UserFollow, User.id == UserFollow.following_id
    ).where(UserFollow.follower_id == current_user.id)
    
    query = query.order_by(UserFollow.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users_data = result.all()
    
    # 获取所有用户的VIP信息
    user_ids = [user.id for user, _ in users_data]
    vip_map = {}
    if user_ids:
        vip_result = await db.execute(
            select(UserVIP).where(
                UserVIP.user_id.in_(user_ids),
                UserVIP.is_active == True
            )
        )
        for vip in vip_result.scalars().all():
            if vip.expire_date and vip.expire_date > datetime.utcnow():
                vip_map[vip.user_id] = vip.vip_level
    
    following = []
    for user, follow in users_data:
        following.append({
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "bio": user.bio,
            "is_following": True,  # 已关注
            "followed_at": follow.created_at,
            "vip_level": vip_map.get(user.id, 0)
        })
    
    # 获取总数
    count_query = select(func.count(UserFollow.id)).where(
        UserFollow.follower_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    return {
        "items": following,
        "total": total
    }


@router.get("/followers")
async def get_followers_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取粉丝列表"""
    from datetime import datetime
    
    # 查找关注当前用户的人
    query = select(User, UserFollow).join(
        UserFollow, User.id == UserFollow.follower_id
    ).where(UserFollow.following_id == current_user.id)
    
    query = query.order_by(UserFollow.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users_data = result.all()
    
    # 获取当前用户关注的人列表，用于判断是否互相关注
    following_result = await db.execute(
        select(UserFollow.following_id).where(UserFollow.follower_id == current_user.id)
    )
    following_ids = {row[0] for row in following_result.all()}
    
    # 获取所有用户的VIP信息
    user_ids = [user.id for user, _ in users_data]
    vip_result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id.in_(user_ids),
            UserVIP.is_active == True
        )
    ) if user_ids else None
    vip_map = {}
    if vip_result:
        for vip in vip_result.scalars().all():
            if vip.expire_date and vip.expire_date > datetime.utcnow():
                vip_map[vip.user_id] = vip.vip_level
    
    followers = []
    for user, follow in users_data:
        followers.append({
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "bio": user.bio,
            "is_following": user.id in following_ids,  # 是否已关注此粉丝
            "followed_at": follow.created_at,
            "vip_level": vip_map.get(user.id, 0)
        })
    
    # 获取总数
    count_query = select(func.count(UserFollow.id)).where(
        UserFollow.following_id == current_user.id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    return {
        "items": followers,
        "total": total
    }


# ==================== 视频合集 ====================

@router.post("/collections")
async def create_collection(
    data: CollectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建视频合集"""
    creator_result = await db.execute(
        select(Creator).where(Creator.user_id == current_user.id)
    )
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(status_code=403, detail="只有创作者可以创建合集")
    
    collection = VideoCollection(
        creator_id=creator.id,
        title=data.title,
        description=data.description,
        pay_type=data.pay_type,
        collection_price=data.collection_price,
        single_video_price=data.single_video_price
    )
    db.add(collection)
    await db.commit()
    
    return {"message": "合集创建成功", "collection_id": collection.id}


@router.get("/collections")
async def get_my_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的合集列表"""
    creator_result = await db.execute(
        select(Creator).where(Creator.user_id == current_user.id)
    )
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        return []
    
    result = await db.execute(
        select(VideoCollection).where(
            VideoCollection.creator_id == creator.id
        ).order_by(VideoCollection.created_at.desc())
    )
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "cover_image": c.cover_image,
            "total_videos": c.total_videos,
            "view_count": c.view_count,
            "subscribe_count": c.subscribe_count,
            "pay_type": c.pay_type,
            "collection_price": c.collection_price,
            "status": c.status,
            "is_completed": c.is_completed
        }
        for c in result.scalars().all()
    ]


@router.post("/collections/{collection_id}/videos")
async def add_video_to_collection(
    collection_id: int,
    video_id: int,
    episode_number: Optional[int] = None,
    episode_title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加视频到合集"""
    # 验证合集所有权
    creator_result = await db.execute(
        select(Creator).where(Creator.user_id == current_user.id)
    )
    creator = creator_result.scalar_one_or_none()
    
    if not creator:
        raise HTTPException(status_code=403, detail="只有创作者可以管理合集")
    
    collection_result = await db.execute(
        select(VideoCollection).where(
            VideoCollection.id == collection_id,
            VideoCollection.creator_id == creator.id
        )
    )
    collection = collection_result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    # 验证视频所有权
    video_result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.uploader_id == current_user.id
        )
    )
    video = video_result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在或无权限")
    
    # 检查是否已在合集中
    existing = await db.execute(
        select(CollectionVideo).where(
            CollectionVideo.collection_id == collection_id,
            CollectionVideo.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="视频已在合集中")
    
    # 添加到合集
    cv = CollectionVideo(
        collection_id=collection_id,
        video_id=video_id,
        episode_number=episode_number or (collection.total_videos + 1),
        episode_title=episode_title or video.title,
        sort_order=collection.total_videos
    )
    db.add(cv)
    
    # 更新合集统计
    collection.total_videos += 1
    collection.total_duration += int(video.duration or 0)
    
    await db.commit()
    
    return {"message": "视频已添加到合集"}
