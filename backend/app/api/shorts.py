"""
短视频 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.video import Video, VideoStatus, ShortVideoCategory
from app.models.user import User, UserVIP
from app.models.social import VideoFavorite, VideoLike
from app.models.coins import VideoPurchase
from app.api.deps import get_current_user, get_current_user_optional


async def check_user_is_vip(db: AsyncSession, user_id: int) -> bool:
    """检查用户是否是有效VIP"""
    from datetime import datetime
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == user_id)
    )
    vip = result.scalar_one_or_none()
    if not vip:
        return False
    return bool(vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow())

# 短视频试看时长（秒）
SHORT_VIDEO_TRIAL_SECONDS = 15

router = APIRouter(prefix="/shorts", tags=["短视频"])


class ShortVideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    video_url: Optional[str] = None
    hls_url: Optional[str] = None
    duration: float = 0
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_vip_only: bool = False
    coin_price: int = 0
    uploader_id: int
    uploader_nickname: Optional[str] = None
    uploader_avatar: Optional[str] = None
    is_liked: bool = False
    is_favorited: bool = False
    is_followed: bool = False  # 是否已关注上传者
    is_purchased: bool = False  # 是否已购买
    trial_seconds: int = 15  # 试看时长（秒）
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShortVideoListResponse(BaseModel):
    items: List[ShortVideoResponse]
    total: int
    page: int
    limit: int
    has_more: bool


@router.get("", response_model=ShortVideoListResponse)
async def get_short_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category_id: Optional[int] = None,  # 兼容旧参数名
    short_category_id: Optional[int] = None,  # 新参数名
    uploader_id: Optional[int] = None,  # 按上传者筛选
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取短视频列表（推荐流）"""
    # 使用 short_category_id，兼容 category_id
    filter_category_id = short_category_id or category_id
    
    # 构建查询
    query = select(Video).where(
        Video.is_short == True,
        Video.status == VideoStatus.PUBLISHED
    ).options(selectinload(Video.uploader))
    
    # 按上传者筛选
    if uploader_id:
        query = query.where(Video.uploader_id == uploader_id)
    
    # 分类筛选（优先使用 short_category_id 字段）
    if filter_category_id:
        query = query.where(Video.short_category_id == filter_category_id)
    
    # 获取总数
    count_base_query = select(Video).where(
        Video.is_short == True,
        Video.status == VideoStatus.PUBLISHED
    )
    if uploader_id:
        count_base_query = count_base_query.where(Video.uploader_id == uploader_id)
    if filter_category_id:
        count_base_query = count_base_query.where(Video.short_category_id == filter_category_id)
    
    count_query = select(func.count()).select_from(count_base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 随机排序：每次刷新获取不同的视频顺序
    query = query.order_by(func.random()).offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    # 获取当前用户的点赞、收藏、关注和购买状态
    liked_ids = set()
    favorited_ids = set()
    followed_ids = set()
    purchased_ids = set()
    is_vip = False
    
    if current_user and videos:
        video_ids = [v.id for v in videos]
        uploader_ids = list({v.uploader_id for v in videos if v.uploader_id})
        
        # 检查VIP状态
        is_vip = await check_user_is_vip(db, current_user.id)
        
        # 获取点赞状态
        likes_result = await db.execute(
            select(VideoLike.video_id).where(
                VideoLike.user_id == current_user.id,
                VideoLike.video_id.in_(video_ids)
            )
        )
        liked_ids = {row[0] for row in likes_result.all()}
        
        # 获取收藏状态
        favorites_result = await db.execute(
            select(VideoFavorite.video_id).where(
                VideoFavorite.user_id == current_user.id,
                VideoFavorite.video_id.in_(video_ids)
            )
        )
        favorited_ids = {row[0] for row in favorites_result.all()}
        
        # 获取关注状态
        if uploader_ids:
            from app.models.creator import UserFollow
            follows_result = await db.execute(
                select(UserFollow.following_id).where(
                    UserFollow.follower_id == current_user.id,
                    UserFollow.following_id.in_(uploader_ids)
                )
            )
            followed_ids = {row[0] for row in follows_result.all()}
        
        # 获取购买状态
        purchases_result = await db.execute(
            select(VideoPurchase.video_id).where(
                VideoPurchase.user_id == current_user.id,
                VideoPurchase.video_id.in_(video_ids)
            )
        )
        purchased_ids = {row[0] for row in purchases_result.all()}
    
    items = []
    for v in videos:
        # 判断是否需要试看限制
        needs_trial = False
        
        # VIP专属视频：VIP用户免费，非VIP用户需试看
        if v.is_vip_only:
            if not is_vip:
                needs_trial = True
            # VIP用户观看VIP专属视频：免费，不需要试看
        else:
            # 非VIP专属视频：有价格且未购买则需试看
            if v.coin_price and v.coin_price > 0 and v.id not in purchased_ids:
                needs_trial = True
        
        items.append(ShortVideoResponse(
            id=v.id,
            title=v.title,
            description=v.description,
            cover_url=v.cover_url,
            video_url=v.original_url or v.hls_url,
            hls_url=v.hls_url,
            duration=v.duration or 0,
            view_count=v.view_count or 0,
            like_count=v.like_count or 0,
            comment_count=v.comment_count or 0,
            share_count=v.share_count or 0,
            is_vip_only=v.is_vip_only or False,
            coin_price=v.coin_price or 0,
            uploader_id=v.uploader_id,
            uploader_nickname=v.uploader.nickname or v.uploader.username if v.uploader else f"用户{v.uploader_id}",
            uploader_avatar=v.uploader.avatar if v.uploader else None,
            is_liked=v.id in liked_ids,
            is_favorited=v.id in favorited_ids,
            is_followed=v.uploader_id in followed_ids,
            is_purchased=v.id in purchased_ids,
            trial_seconds=SHORT_VIDEO_TRIAL_SECONDS if needs_trial else 0,
            created_at=v.created_at
        ))
    
    return ShortVideoListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_more=(page * limit) < total
    )


# ============== 短视频分类 API ==============
# 注意：此路由必须在 /{video_id} 之前定义，否则 "categories" 会被当作 video_id 解析

class ShortCategoryResponse(BaseModel):
    """短视频分类响应"""
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    video_count: int = 0
    
    class Config:
        from_attributes = True


@router.get("/categories", response_model=List[ShortCategoryResponse])
async def get_short_categories(
    db: AsyncSession = Depends(get_db)
):
    """获取短视频分类列表"""
    result = await db.execute(
        select(ShortVideoCategory)
        .where(ShortVideoCategory.is_active == True)
        .order_by(ShortVideoCategory.sort_order.asc(), ShortVideoCategory.id.asc())
    )
    categories = result.scalars().all()
    
    # 获取每个分类的视频数量
    response = []
    for cat in categories:
        count_result = await db.execute(
            select(func.count(Video.id)).where(
                Video.short_category_id == cat.id,
                Video.is_short == True,
                Video.status == VideoStatus.PUBLISHED
            )
        )
        video_count = count_result.scalar() or 0
        
        response.append(ShortCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            icon=cat.icon,
            sort_order=cat.sort_order or 0,
            video_count=video_count
        ))
    
    return response


@router.get("/{video_id}", response_model=ShortVideoResponse)
async def get_short_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取单个短视频详情"""
    result = await db.execute(
        select(Video).where(
            Video.id == video_id,
            Video.is_short == True,
            Video.status == VideoStatus.PUBLISHED
        ).options(selectinload(Video.uploader))
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 增加播放量
    video.view_count = (video.view_count or 0) + 1
    await db.commit()
    
    # 检查点赞、收藏、关注和购买状态
    is_liked = False
    is_favorited = False
    is_followed = False
    is_purchased = False
    is_vip = False
    
    if current_user:
        is_vip = await check_user_is_vip(db, current_user.id)
        
        like_result = await db.execute(
            select(VideoLike).where(
                VideoLike.user_id == current_user.id,
                VideoLike.video_id == video_id
            ).limit(1)
        )
        is_liked = like_result.scalar() is not None
        
        fav_result = await db.execute(
            select(VideoFavorite).where(
                VideoFavorite.user_id == current_user.id,
                VideoFavorite.video_id == video_id
            ).limit(1)
        )
        is_favorited = fav_result.scalar() is not None
        
        # 检查关注状态
        from app.models.creator import UserFollow
        follow_result = await db.execute(
            select(UserFollow).where(
                UserFollow.follower_id == current_user.id,
                UserFollow.following_id == video.uploader_id
            ).limit(1)
        )
        is_followed = follow_result.scalar() is not None
        
        # 检查购买状态
        purchase_result = await db.execute(
            select(VideoPurchase).where(
                VideoPurchase.user_id == current_user.id,
                VideoPurchase.video_id == video_id
            ).limit(1)
        )
        is_purchased = purchase_result.scalar() is not None
    
    # 判断是否需要试看限制
    needs_trial = False
    
    # VIP专属视频：VIP用户免费，非VIP用户需试看
    if video.is_vip_only:
        if not is_vip:
            needs_trial = True
        # VIP用户观看VIP专属视频：免费，不需要试看
    else:
        # 非VIP专属视频：有价格且未购买则需试看
        if video.coin_price and video.coin_price > 0 and not is_purchased:
            needs_trial = True
    
    return ShortVideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        cover_url=video.cover_url,
        video_url=video.original_url or video.hls_url,
        hls_url=video.hls_url,
        duration=video.duration or 0,
        view_count=video.view_count or 0,
        like_count=video.like_count or 0,
        comment_count=video.comment_count or 0,
        share_count=video.share_count or 0,
        is_vip_only=video.is_vip_only or False,
        coin_price=video.coin_price or 0,
        uploader_id=video.uploader_id,
        uploader_nickname=video.uploader.nickname or video.uploader.username if video.uploader else f"用户{video.uploader_id}",
        uploader_avatar=video.uploader.avatar if video.uploader else None,
        is_liked=is_liked,
        is_favorited=is_favorited,
        is_followed=is_followed,
        is_purchased=is_purchased,
        trial_seconds=SHORT_VIDEO_TRIAL_SECONDS if needs_trial else 0,
        created_at=video.created_at
    )


@router.post("/{video_id}/like")
async def like_short_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """点赞短视频"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已点赞
    existing_result = await db.execute(
        select(VideoLike).where(
            VideoLike.user_id == current_user.id,
            VideoLike.video_id == video_id
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # 取消点赞
        await db.delete(existing)
        video.like_count = max(0, (video.like_count or 0) - 1)
        await db.commit()
        return {"liked": False, "like_count": video.like_count}
    else:
        # 点赞
        like = VideoLike(user_id=current_user.id, video_id=video_id)
        db.add(like)
        video.like_count = (video.like_count or 0) + 1
        await db.commit()
        return {"liked": True, "like_count": video.like_count}


@router.post("/{video_id}/favorite")
async def favorite_short_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """收藏短视频"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已收藏
    existing_result = await db.execute(
        select(VideoFavorite).where(
            VideoFavorite.user_id == current_user.id,
            VideoFavorite.video_id == video_id
        )
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        # 取消收藏
        await db.delete(existing)
        await db.commit()
        return {"favorited": False}
    else:
        # 收藏
        favorite = VideoFavorite(user_id=current_user.id, video_id=video_id)
        db.add(favorite)
        await db.commit()
        return {"favorited": True}


# ========== VIP下载功能 ==========

from fastapi.responses import FileResponse
from app.core.vip_benefits import get_daily_download_limit, can_download
import os

@router.get("/{video_id}/download-info")
async def get_short_download_info(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取短视频下载信息（检查是否可下载）
    """
    # 检查用户是否是VIP
    is_vip = await check_user_is_vip(db, current_user.id)
    
    # 获取视频
    result = await db.execute(select(Video).where(Video.id == video_id, Video.is_short == True))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=404,
            detail="短视频不存在"
        )
    
    # 获取视频文件路径 - 处理绝对路径和相对路径
    video_path = None
    file_exists = False
    
    if video.original_url:
        path = video.original_url
        if os.path.isabs(path):
            if os.path.exists(path):
                video_path = path
                file_exists = True
        else:
            if path.startswith('/uploads'):
                path = os.path.join(os.getcwd(), path.lstrip('/'))
            elif path.startswith('uploads'):
                path = os.path.join(os.getcwd(), path)
            if os.path.exists(path):
                video_path = path
                file_exists = True
    
    # 从original_url提取文件名查找
    if not file_exists and video.original_url:
        import re
        match = re.search(r'([a-f0-9\-]{36}\.mp4)', video.original_url, re.IGNORECASE)
        if match:
            from app.core.config import settings
            filename = match.group(1)
            possible_path = os.path.join(settings.VIDEO_DIR, filename)
            if os.path.exists(possible_path):
                video_path = possible_path
                file_exists = True
    
    file_size = os.path.getsize(video_path) if file_exists else 0
    
    return {
        "video_id": video_id,
        "title": video.title,
        "can_download": is_vip and file_exists,
        "is_vip": is_vip,
        "file_exists": file_exists,
        "file_size": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size else 0,
        "message": "可以下载" if (is_vip and file_exists) else ("请开通VIP" if not is_vip else "文件不存在")
    }


@router.get("/{video_id}/download")
async def download_short_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    VIP专属：下载短视频
    返回视频文件的直接下载链接
    包含每日下载次数限制
    """
    # 检查用户VIP状态
    result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id == current_user.id,
            UserVIP.is_active == True,
            UserVIP.expire_date > datetime.utcnow()
        )
    )
    vip = result.scalar_one_or_none()
    
    if not vip:
        raise HTTPException(
            status_code=403,
            detail="下载功能仅限VIP会员使用"
        )
    
    vip_level = getattr(vip, 'vip_level', 1) or 1
    
    # 检查VIP等级是否支持下载
    if not can_download(vip_level):
        raise HTTPException(
            status_code=403,
            detail="您的VIP等级不支持下载功能，请升级VIP"
        )
    
    # 检查每日下载次数限制
    from app.core.redis import RedisCache
    today = datetime.utcnow().strftime("%Y-%m-%d")
    download_key = f"user_downloads:{current_user.id}:{today}"
    
    try:
        today_downloads = await RedisCache.get(download_key)
        today_downloads = int(today_downloads) if today_downloads else 0
    except:
        today_downloads = 0
    
    daily_limit = get_daily_download_limit(vip_level)
    
    if daily_limit > 0 and today_downloads >= daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"今日下载次数已达上限（{daily_limit}次），请明日再试"
        )
    
    # 获取视频
    result = await db.execute(select(Video).where(Video.id == video_id, Video.is_short == True))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=404,
            detail="短视频不存在"
        )
    
    # 获取原始视频文件路径 - 处理绝对路径和相对路径
    video_path = None
    file_exists = False
    
    if video.original_url:
        path = video.original_url
        if os.path.isabs(path):
            if os.path.exists(path):
                video_path = path
                file_exists = True
        else:
            if path.startswith('/uploads'):
                path = os.path.join(os.getcwd(), path.lstrip('/'))
            elif path.startswith('uploads'):
                path = os.path.join(os.getcwd(), path)
            if os.path.exists(path):
                video_path = path
                file_exists = True
    
    # 从original_url提取文件名查找
    if not file_exists and video.original_url:
        import re
        from app.core.config import settings
        match = re.search(r'([a-f0-9\-]{36}\.mp4)', video.original_url, re.IGNORECASE)
        if match:
            filename = match.group(1)
            possible_path = os.path.join(settings.VIDEO_DIR, filename)
            if os.path.exists(possible_path):
                video_path = possible_path
                file_exists = True
    
    if not file_exists:
        raise HTTPException(
            status_code=404,
            detail="视频文件不存在"
        )
    
    # 记录下载次数
    try:
        await RedisCache.incr(download_key)
        await RedisCache.expire(download_key, 86400)  # 24小时
    except:
        pass  # Redis故障不影响下载
    
    # 生成下载文件名
    filename = f"{video.title}.mp4"
    # 移除特殊字符
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
    if not filename:
        filename = f"short_{video_id}.mp4"
    
    # 返回文件下载
    return FileResponse(
        path=video_path,
        filename=filename,
        media_type='video/mp4',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


