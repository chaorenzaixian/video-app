"""
通知相关 API
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.video import Video
from app.models.comment import Comment, CommentLike
from app.models.social import VideoLike, UserNotification
from app.models.user import UserVIP

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationItem(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    content: Optional[str] = None
    video_id: Optional[int] = None
    video_title: Optional[str] = None
    is_short: bool = False
    type: str = "video"  # video or comment
    is_vip: bool = False
    vip_level: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


async def get_user_vip_info(db: AsyncSession, user_id: int) -> tuple:
    """获取用户VIP信息"""
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
    return is_vip, vip_level


class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    total: int
    unread_count: int


@router.get("/comments", response_model=NotificationListResponse)
async def get_comment_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评论通知 - 别人对我的视频的评论"""
    
    # 获取当前用户的所有视频ID
    user_videos_query = select(Video.id).where(Video.uploader_id == current_user.id)
    user_videos_result = await db.execute(user_videos_query)
    user_video_ids = [row[0] for row in user_videos_result.fetchall()]
    
    if not user_video_ids:
        return NotificationListResponse(items=[], total=0, unread_count=0)
    
    # 查询别人对我视频的评论（排除自己的评论）
    query = (
        select(Comment, User, Video)
        .join(User, Comment.user_id == User.id)
        .join(Video, Comment.video_id == Video.id)
        .where(
            and_(
                Comment.video_id.in_(user_video_ids),
                Comment.user_id != current_user.id,
                Comment.is_hidden == False
            )
        )
        .order_by(desc(Comment.created_at))
    )
    
    # 获取总数
    count_query = (
        select(func.count(Comment.id))
        .where(
            and_(
                Comment.video_id.in_(user_video_ids),
                Comment.user_id != current_user.id,
                Comment.is_hidden == False
            )
        )
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    items = []
    for comment, user, video in rows:
        # 获取用户VIP信息
        is_vip, vip_level = await get_user_vip_info(db, user.id)
        items.append(NotificationItem(
            id=comment.id,
            user_id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            content=comment.content[:50] + ('...' if len(comment.content) > 50 else ''),
            video_id=video.id,
            video_title=video.title,
            is_short=video.is_short or False,
            type="video",
            is_vip=is_vip,
            vip_level=vip_level,
            created_at=comment.created_at
        ))
    
    # 未读数（简化处理，这里返回最近24小时的评论数）
    unread_count = 0
    
    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count
    )


@router.get("/likes", response_model=NotificationListResponse)
async def get_like_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取点赞通知 - 别人对我的视频的点赞"""
    
    # 获取当前用户的所有视频ID
    user_videos_query = select(Video.id).where(Video.uploader_id == current_user.id)
    user_videos_result = await db.execute(user_videos_query)
    user_video_ids = [row[0] for row in user_videos_result.fetchall()]
    
    if not user_video_ids:
        return NotificationListResponse(items=[], total=0, unread_count=0)
    
    # 查询别人对我视频的点赞（排除自己）
    query = (
        select(VideoLike, User, Video)
        .join(User, VideoLike.user_id == User.id)
        .join(Video, VideoLike.video_id == Video.id)
        .where(
            and_(
                VideoLike.video_id.in_(user_video_ids),
                VideoLike.user_id != current_user.id
            )
        )
        .order_by(desc(VideoLike.created_at))
    )
    
    # 获取总数
    count_query = (
        select(func.count(VideoLike.id))
        .where(
            and_(
                VideoLike.video_id.in_(user_video_ids),
                VideoLike.user_id != current_user.id
            )
        )
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    items = []
    for like, user, video in rows:
        # 获取用户VIP信息
        is_vip, vip_level = await get_user_vip_info(db, user.id)
        items.append(NotificationItem(
            id=like.id,
            user_id=user.id,
            username=user.username,
            nickname=user.nickname,
            avatar=user.avatar,
            content=None,
            video_id=video.id,
            video_title=video.title,
            is_short=video.is_short or False,
            type="video",
            is_vip=is_vip,
            vip_level=vip_level,
            created_at=like.created_at
        ))
    
    # 未读数
    unread_count = 0
    
    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取未读通知总数（私信、评论、点赞）"""
    from app.models.social import MessageConversation
    
    # 1. 私信未读数 - 从会话表统计
    private_unread = 0
    try:
        conv_query = select(MessageConversation).where(
            or_(
                MessageConversation.user1_id == current_user.id,
                MessageConversation.user2_id == current_user.id
            )
        )
        conv_result = await db.execute(conv_query)
        conversations = conv_result.scalars().all()
        
        for conv in conversations:
            if conv.user1_id == current_user.id:
                private_unread += conv.user1_unread or 0
            else:
                private_unread += conv.user2_unread or 0
    except Exception as e:
        print(f"获取私信未读数失败: {e}")
    
    # 2. 评论未读数 - 查询最近24小时对我视频的评论
    comment_unread = 0
    try:
        user_videos_result = await db.execute(
            select(Video.id).where(Video.uploader_id == current_user.id)
        )
        user_video_ids = [row[0] for row in user_videos_result.fetchall()]
        
        if user_video_ids:
            yesterday = datetime.utcnow() - timedelta(hours=24)
            comment_query = select(func.count(Comment.id)).where(
                and_(
                    Comment.video_id.in_(user_video_ids),
                    Comment.user_id != current_user.id,
                    Comment.is_hidden == False,
                    Comment.created_at >= yesterday
                )
            )
            comment_result = await db.execute(comment_query)
            comment_unread = comment_result.scalar() or 0
    except Exception as e:
        print(f"获取评论未读数失败: {e}")
    
    # 3. 点赞未读数 - 查询最近24小时对我视频的点赞
    like_unread = 0
    try:
        if user_video_ids:
            yesterday = datetime.utcnow() - timedelta(hours=24)
            like_query = select(func.count(VideoLike.id)).where(
                and_(
                    VideoLike.video_id.in_(user_video_ids),
                    VideoLike.user_id != current_user.id,
                    VideoLike.created_at >= yesterday
                )
            )
            like_result = await db.execute(like_query)
            like_unread = like_result.scalar() or 0
    except Exception as e:
        print(f"获取点赞未读数失败: {e}")
    
    total = private_unread + comment_unread + like_unread
    
    return {
        "private_messages": private_unread,
        "comments": comment_unread,
        "likes": like_unread,
        "total": total
    }


@router.post("/mark-read")
async def mark_notifications_read(
    notification_type: str = Query(..., description="通知类型: private, comment, like, all"),
    target_user_id: Optional[int] = Query(None, description="目标用户ID（仅私信时有效）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记通知为已读"""
    from app.models.social import MessageConversation
    
    result = {"success": True, "message": "已标记为已读"}
    
    try:
        if notification_type in ['private', 'all']:
            # 构建查询条件
            if target_user_id:
                # 标记特定会话为已读
                conv_query = select(MessageConversation).where(
                    or_(
                        and_(
                            MessageConversation.user1_id == current_user.id,
                            MessageConversation.user2_id == target_user_id
                        ),
                        and_(
                            MessageConversation.user1_id == target_user_id,
                            MessageConversation.user2_id == current_user.id
                        )
                    )
                )
            else:
                # 标记所有会话为已读
                conv_query = select(MessageConversation).where(
                    or_(
                        MessageConversation.user1_id == current_user.id,
                        MessageConversation.user2_id == current_user.id
                    )
                )
            
            conv_result = await db.execute(conv_query)
            conversations = conv_result.scalars().all()
            
            for conv in conversations:
                if conv.user1_id == current_user.id:
                    conv.user1_unread = 0
                else:
                    conv.user2_unread = 0
            
            await db.commit()
        
        # 评论和点赞没有实际的未读标记存储，只是基于时间统计
        # 所以这里只需要返回成功即可，前端会清除显示
        
    except Exception as e:
        print(f"标记已读失败: {e}")
        result = {"success": False, "message": str(e)}
    
    return result



