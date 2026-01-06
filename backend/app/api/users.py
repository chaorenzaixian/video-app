"""
用户相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User, UserVIP
from app.models.video import Video, VideoView
from app.models.promotion import UserProfile, Reward
from app.models.creator import UserFollow
from app.schemas.user import UserResponse, UserUpdate, VIPInfo, InviteInfo


# ===== 响应模型 =====
class VideoHistoryItem(BaseModel):
    id: int
    video_id: int
    title: str
    cover_url: Optional[str] = None
    duration: Optional[float] = None
    watch_progress: float = 0
    watch_duration: float = 0
    watched_at: datetime
    
    class Config:
        from_attributes = True


class VideoFavoriteItem(BaseModel):
    id: int
    title: str
    cover_url: Optional[str] = None
    duration: Optional[float] = None
    view_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

router = APIRouter()


# 导入VIP配置
from app.core.vip_config import get_vip_level_name, get_vip_level_icon

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    # 获取VIP信息
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id)
    )
    vip = result.scalar_one_or_none()
    
    is_vip = False
    vip_expire_date = None
    vip_level = 0
    vip_level_name = "非VIP"
    
    if vip:
        vip_expire_date = vip.expire_date
        
        # 判断VIP是否有效（需要激活且未过期）
        if vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
            is_vip = True
            # 只有VIP有效时才显示等级，如果等级为0则默认为1（普通VIP）
            vip_level = getattr(vip, 'vip_level', 0) or 0
            if vip_level == 0:
                vip_level = 1  # 激活状态下默认至少是普通VIP
            vip_level_name = get_vip_level_name(vip_level)
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        nickname=current_user.nickname,
        avatar=current_user.avatar,
        bio=current_user.bio,
        gender=current_user.gender,
        role=current_user.role,
        invite_code=current_user.invite_code,
        invite_count=current_user.invite_count,
        is_vip=is_vip,
        is_guest=getattr(current_user, 'is_guest', False),
        vip_level=vip_level,
        vip_level_name=vip_level_name,
        vip_expire_date=vip_expire_date,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    if user_in.nickname is not None:
        current_user.nickname = user_in.nickname
    if user_in.avatar is not None:
        current_user.avatar = user_in.avatar
    if user_in.bio is not None:
        current_user.bio = user_in.bio
    if user_in.gender is not None:
        current_user.gender = user_in.gender
    if user_in.email is not None:
        # 检查邮箱是否已被其他用户使用
        result = await db.execute(
            select(User).where(User.email == user_in.email)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被其他账号绑定"
            )
        current_user.email = user_in.email
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return await get_current_user_info(current_user, db)


@router.get("/me/vip", response_model=VIPInfo)
async def get_vip_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取VIP信息"""
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id)
    )
    vip = result.scalar_one_or_none()
    
    if not vip:
        return VIPInfo(is_active=False)
    
    is_active = vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow()
    
    return VIPInfo(
        is_active=is_active,
        vip_type=vip.vip_type,
        start_date=vip.start_date,
        expire_date=vip.expire_date,
        total_days=vip.total_days
    )


@router.get("/me/invite", response_model=InviteInfo)
async def get_invite_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取邀请信息"""
    # 获取用户推广资料
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if profile:
        invite_code = profile.invite_code
        invite_count = profile.total_invites
        total_reward_days = profile.total_reward_days
    else:
        # 兼容旧用户
        invite_code = current_user.invite_code
        invite_count = current_user.invite_count
        # 从Reward表计算总奖励天数
        result = await db.execute(
            select(func.sum(Reward.reward_value)).where(
                Reward.user_id == current_user.id,
                Reward.reward_content == "vip_days",
                Reward.claimed == True
            )
        )
        total_reward_days = int(result.scalar() or 0)
    
    return InviteInfo(
        invite_code=invite_code,
        invite_count=invite_count,
        total_reward_days=total_reward_days
    )


@router.get("/me/history")
async def get_watch_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户观看历史"""
    offset = (page - 1) * page_size
    
    # 获取观看记录并关联视频信息
    query = (
        select(VideoView)
        .options(selectinload(VideoView.video))
        .where(VideoView.user_id == current_user.id)
        .order_by(desc(VideoView.created_at))
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    views = result.scalars().all()
    
    # 统计总数
    count_result = await db.execute(
        select(func.count(VideoView.id)).where(VideoView.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    items = []
    for view in views:
        if view.video:
            items.append(VideoHistoryItem(
                id=view.id,
                video_id=view.video_id,
                title=view.video.title,
                cover_url=view.video.cover_url,
                duration=view.video.duration,
                watch_progress=view.watch_progress or 0,
                watch_duration=view.watch_duration or 0,
                watched_at=view.created_at
            ))
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/me/favorites")
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户收藏列表
    
    注意：当前系统使用观看记录作为收藏的简单实现
    如需完整收藏功能，需要创建单独的VideoFavorite模型
    """
    offset = (page - 1) * page_size
    
    # 使用子查询去重，获取每个视频最新的观看记录
    from sqlalchemy import and_
    
    subquery = (
        select(
            VideoView.video_id,
            func.max(VideoView.created_at).label('latest')
        )
        .where(VideoView.user_id == current_user.id)
        .group_by(VideoView.video_id)
        .subquery()
    )
    
    query = (
        select(Video)
        .join(subquery, Video.id == subquery.c.video_id)
        .order_by(desc(subquery.c.latest))
        .offset(offset)
        .limit(page_size)
    )
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    # 统计总数（去重后的视频数）
    count_result = await db.execute(
        select(func.count(func.distinct(VideoView.video_id)))
        .where(VideoView.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    
    items = [
        VideoFavoriteItem(
            id=video.id,
            title=video.title,
            cover_url=video.cover_url,
            duration=video.duration,
            view_count=video.view_count,
            created_at=video.created_at
        )
        for video in videos
    ]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.delete("/me/history/{view_id}")
async def delete_history_item(
    view_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除单条观看记录"""
    result = await db.execute(
        select(VideoView).where(
            VideoView.id == view_id,
            VideoView.user_id == current_user.id
        )
    )
    view = result.scalar_one_or_none()
    
    if not view:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    await db.delete(view)
    await db.commit()
    
    return {"message": "删除成功"}


@router.delete("/me/history")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """清空观看历史"""
    from sqlalchemy import delete
    await db.execute(
        delete(VideoView).where(VideoView.user_id == current_user.id)
    )
    await db.commit()
    
    return {"message": "历史已清空"}


class UserProfileResponse(BaseModel):
    """用户主页响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    video_count: int = 0
    fans_count: int = 0
    following_count: int = 0
    is_followed: bool = False
    is_vip: bool = False
    vip_level: int = 0
    
    class Config:
        from_attributes = True


# 注意：更具体的路由 /{user_id}/profile 必须在 /{user_id} 之前定义
@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取用户主页信息"""
    # 获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取视频数量
    from app.models.video import VideoStatus
    video_count_result = await db.execute(
        select(func.count(Video.id)).where(
            Video.uploader_id == user_id,
            Video.status == VideoStatus.PUBLISHED
        )
    )
    video_count = video_count_result.scalar() or 0
    
    # 获取粉丝数量
    fans_result = await db.execute(
        select(func.count(UserFollow.id)).where(UserFollow.following_id == user_id)
    )
    fans_count = fans_result.scalar() or 0
    
    # 获取关注数量
    following_result = await db.execute(
        select(func.count(UserFollow.id)).where(UserFollow.follower_id == user_id)
    )
    following_count = following_result.scalar() or 0
    
    # 检查当前用户是否已关注
    is_followed = False
    if current_user:
        follow_check = await db.execute(
            select(UserFollow).where(
                UserFollow.follower_id == current_user.id,
                UserFollow.following_id == user_id
            ).limit(1)
        )
        is_followed = follow_check.scalar_one_or_none() is not None
    
    # 获取VIP信息
    from datetime import datetime
    vip_result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id == user_id,
            UserVIP.is_active == True
        )
    )
    user_vip = vip_result.scalar_one_or_none()
    is_vip = False
    vip_level = 0
    if user_vip and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
        is_vip = True
        vip_level = user_vip.vip_level or 1
    
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,  # 使用用户名作为fallback
        avatar=user.avatar,
        bio=user.bio,
        video_count=video_count,
        fans_count=fans_count,
        following_count=following_count,
        is_followed=is_followed,
        is_vip=is_vip,
        vip_level=vip_level
    )


@router.post("/{user_id}/follow")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """关注用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    
    # 检查用户是否存在
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查是否已关注（使用first()避免多条记录报错）
    follow_result = await db.execute(
        select(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == user_id
        ).limit(1)
    )
    existing_follow = follow_result.scalar_one_or_none()
    
    if existing_follow:
        # 已关注，返回成功
        return {"followed": True, "message": "已关注"}
    
    # 创建关注关系
    follow = UserFollow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    await db.commit()
    return {"followed": True, "message": "关注成功"}


@router.delete("/{user_id}/follow")
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消关注用户"""
    # 删除所有关注记录（处理可能的重复数据）
    from sqlalchemy import delete
    await db.execute(
        delete(UserFollow).where(
            UserFollow.follower_id == current_user.id,
            UserFollow.following_id == user_id
        )
    )
    await db.commit()
    
    return {"followed": False, "message": "已取消关注"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户公开信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email="***",  # 隐藏邮箱
        nickname=user.nickname,
        avatar=user.avatar,
        bio=user.bio,
        role=user.role,
        invite_code="",  # 不展示邀请码
        invite_count=user.invite_count,
        created_at=user.created_at
    )