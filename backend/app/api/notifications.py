"""
通知相关 API - 支持所有栏目的评论和点赞通知
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserVIP
from app.models.video import Video
from app.models.comment import Comment, CommentLike
from app.models.social import VideoLike
from app.models.community import (
    Post, PostComment, PostLike, PostCommentLike,
    Gallery, GalleryComment, GalleryLike, GalleryCommentLike,
    Novel, NovelLike
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationItem(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    content: Optional[str] = None
    target_id: Optional[int] = None
    target_title: Optional[str] = None
    target_type: str = "video"  # video, short, post, gallery, novel
    notification_type: str = "comment"  # comment, reply, like
    is_vip: bool = False
    vip_level: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    total: int
    unread_count: int


async def get_user_vip_info(db: AsyncSession, user_id: int) -> tuple:
    """获取用户VIP信息"""
    try:
        vip_result = await db.execute(
            select(UserVIP).where(
                UserVIP.user_id == user_id,
                UserVIP.is_active == True
            )
        )
        user_vip = vip_result.scalar_one_or_none()
        if user_vip and user_vip.expire_date and user_vip.expire_date > datetime.utcnow():
            return True, user_vip.vip_level or 1
    except:
        pass
    return False, 0


@router.get("/comments", response_model=NotificationListResponse)
async def get_comment_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评论通知 - 所有栏目的评论和回复"""
    try:
        items = []
        
        # ========== 1. 视频评论通知 ==========
        user_videos_result = await db.execute(
            select(Video.id).where(Video.uploader_id == current_user.id)
        )
        user_video_ids = [row[0] for row in user_videos_result.fetchall()]
        
        if user_video_ids:
            video_comments_query = (
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
                .limit(50)
            )
            result = await db.execute(video_comments_query)
            for comment, user, video in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': comment.id,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (comment.content or '')[:50],
                    'target_id': video.id,
                    'target_title': video.title,
                    'target_type': 'short' if video.is_short else 'video',
                    'notification_type': 'comment',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': comment.created_at
                })
        
        # 视频评论回复
        my_video_comments_result = await db.execute(
            select(Comment.id).where(Comment.user_id == current_user.id)
        )
        my_video_comment_ids = [row[0] for row in my_video_comments_result.fetchall()]
        
        if my_video_comment_ids:
            video_replies_query = (
                select(Comment, User, Video)
                .join(User, Comment.user_id == User.id)
                .join(Video, Comment.video_id == Video.id)
                .where(
                    and_(
                        Comment.parent_id.in_(my_video_comment_ids),
                        Comment.user_id != current_user.id,
                        Comment.is_hidden == False
                    )
                )
                .order_by(desc(Comment.created_at))
                .limit(50)
            )
            result = await db.execute(video_replies_query)
            for reply, user, video in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': reply.id + 100000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (reply.content or '')[:50],
                    'target_id': video.id,
                    'target_title': video.title,
                    'target_type': 'short' if video.is_short else 'video',
                    'notification_type': 'reply',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': reply.created_at
                })
        
        # ========== 2. 帖子评论通知 ==========
        user_posts_result = await db.execute(
            select(Post.id).where(Post.user_id == current_user.id)
        )
        user_post_ids = [row[0] for row in user_posts_result.fetchall()]
        
        if user_post_ids:
            post_comments_query = (
                select(PostComment, User, Post)
                .join(User, PostComment.user_id == User.id)
                .join(Post, PostComment.post_id == Post.id)
                .where(
                    and_(
                        PostComment.post_id.in_(user_post_ids),
                        PostComment.user_id != current_user.id,
                        PostComment.status == 'visible'
                    )
                )
                .order_by(desc(PostComment.created_at))
                .limit(50)
            )
            result = await db.execute(post_comments_query)
            for comment, user, post in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                post_title = (post.content[:20] if post.content else '帖子')
                items.append({
                    'id': comment.id + 1000000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (comment.content or '')[:50],
                    'target_id': post.id,
                    'target_title': post_title,
                    'target_type': 'post',
                    'notification_type': 'comment',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': comment.created_at
                })
        
        # 帖子评论回复
        my_post_comments_result = await db.execute(
            select(PostComment.id).where(PostComment.user_id == current_user.id)
        )
        my_post_comment_ids = [row[0] for row in my_post_comments_result.fetchall()]
        
        if my_post_comment_ids:
            post_replies_query = (
                select(PostComment, User, Post)
                .join(User, PostComment.user_id == User.id)
                .join(Post, PostComment.post_id == Post.id)
                .where(
                    and_(
                        PostComment.parent_id.in_(my_post_comment_ids),
                        PostComment.user_id != current_user.id,
                        PostComment.status == 'visible'
                    )
                )
                .order_by(desc(PostComment.created_at))
                .limit(50)
            )
            result = await db.execute(post_replies_query)
            for reply, user, post in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                post_title = (post.content[:20] if post.content else '帖子')
                items.append({
                    'id': reply.id + 1100000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (reply.content or '')[:50],
                    'target_id': post.id,
                    'target_title': post_title,
                    'target_type': 'post',
                    'notification_type': 'reply',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': reply.created_at
                })
        
        # ========== 3. 图集评论通知 ==========
        # 图集没有 user_id，跳过图集评论通知（图集是系统内容）
        # 但可以获取别人回复我的图集评论
        my_gallery_comments_result = await db.execute(
            select(GalleryComment.id).where(GalleryComment.user_id == current_user.id)
        )
        my_gallery_comment_ids = [row[0] for row in my_gallery_comments_result.fetchall()]
        
        if my_gallery_comment_ids:
            gallery_replies_query = (
                select(GalleryComment, User, Gallery)
                .join(User, GalleryComment.user_id == User.id)
                .join(Gallery, GalleryComment.gallery_id == Gallery.id)
                .where(
                    and_(
                        GalleryComment.parent_id.in_(my_gallery_comment_ids),
                        GalleryComment.user_id != current_user.id,
                        GalleryComment.is_hidden == False
                    )
                )
                .order_by(desc(GalleryComment.created_at))
                .limit(50)
            )
            result = await db.execute(gallery_replies_query)
            for reply, user, gallery in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': reply.id + 2000000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (reply.content or '')[:50],
                    'target_id': gallery.id,
                    'target_title': gallery.title,
                    'target_type': 'gallery',
                    'notification_type': 'reply',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': reply.created_at
                })
        
        # 按时间排序并分页
        items.sort(key=lambda x: x['created_at'], reverse=True)
        total = len(items)
        offset = (page - 1) * page_size
        items = items[offset:offset + page_size]
        
        return NotificationListResponse(
            items=[NotificationItem(**item) for item in items],
            total=total,
            unread_count=0
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/likes", response_model=NotificationListResponse)
async def get_like_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取点赞通知 - 所有栏目的点赞"""
    try:
        items = []
        
        # ========== 1. 视频点赞通知 ==========
        user_videos_result = await db.execute(
            select(Video.id).where(Video.uploader_id == current_user.id)
        )
        user_video_ids = [row[0] for row in user_videos_result.fetchall()]
        
        if user_video_ids:
            video_likes_query = (
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
                .limit(50)
            )
            result = await db.execute(video_likes_query)
            for like, user, video in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': like.id,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': None,
                    'target_id': video.id,
                    'target_title': video.title,
                    'target_type': 'short' if video.is_short else 'video',
                    'notification_type': 'like',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': like.created_at
                })
        
        # 视频评论点赞
        my_video_comments_result = await db.execute(
            select(Comment.id).where(Comment.user_id == current_user.id)
        )
        my_video_comment_ids = [row[0] for row in my_video_comments_result.fetchall()]
        
        if my_video_comment_ids:
            video_comment_likes_query = (
                select(CommentLike, User, Comment)
                .join(User, CommentLike.user_id == User.id)
                .join(Comment, CommentLike.comment_id == Comment.id)
                .where(
                    and_(
                        CommentLike.comment_id.in_(my_video_comment_ids),
                        CommentLike.user_id != current_user.id
                    )
                )
                .order_by(desc(CommentLike.created_at))
                .limit(50)
            )
            result = await db.execute(video_comment_likes_query)
            for like, user, comment in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': like.id + 100000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (comment.content or '')[:30],
                    'target_id': comment.video_id,
                    'target_title': None,
                    'target_type': 'video_comment',
                    'notification_type': 'like',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': like.created_at
                })
        
        # ========== 2. 帖子点赞通知 ==========
        user_posts_result = await db.execute(
            select(Post.id).where(Post.user_id == current_user.id)
        )
        user_post_ids = [row[0] for row in user_posts_result.fetchall()]
        
        if user_post_ids:
            post_likes_query = (
                select(PostLike, User, Post)
                .join(User, PostLike.user_id == User.id)
                .join(Post, PostLike.post_id == Post.id)
                .where(
                    and_(
                        PostLike.post_id.in_(user_post_ids),
                        PostLike.user_id != current_user.id
                    )
                )
                .order_by(desc(PostLike.created_at))
                .limit(50)
            )
            result = await db.execute(post_likes_query)
            for like, user, post in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                post_title = (post.content[:20] if post.content else '帖子')
                items.append({
                    'id': like.id + 1000000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': None,
                    'target_id': post.id,
                    'target_title': post_title,
                    'target_type': 'post',
                    'notification_type': 'like',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': like.created_at
                })
        
        # 帖子评论点赞
        my_post_comments_result = await db.execute(
            select(PostComment.id).where(PostComment.user_id == current_user.id)
        )
        my_post_comment_ids = [row[0] for row in my_post_comments_result.fetchall()]
        
        if my_post_comment_ids:
            post_comment_likes_query = (
                select(PostCommentLike, User, PostComment)
                .join(User, PostCommentLike.user_id == User.id)
                .join(PostComment, PostCommentLike.comment_id == PostComment.id)
                .where(
                    and_(
                        PostCommentLike.comment_id.in_(my_post_comment_ids),
                        PostCommentLike.user_id != current_user.id
                    )
                )
                .order_by(desc(PostCommentLike.created_at))
                .limit(50)
            )
            result = await db.execute(post_comment_likes_query)
            for like, user, comment in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': like.id + 1100000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (comment.content or '')[:30],
                    'target_id': comment.post_id,
                    'target_title': None,
                    'target_type': 'post_comment',
                    'notification_type': 'like',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': like.created_at
                })
        
        # ========== 3. 图集评论点赞 ==========
        my_gallery_comments_result = await db.execute(
            select(GalleryComment.id).where(GalleryComment.user_id == current_user.id)
        )
        my_gallery_comment_ids = [row[0] for row in my_gallery_comments_result.fetchall()]
        
        if my_gallery_comment_ids:
            gallery_comment_likes_query = (
                select(GalleryCommentLike, User, GalleryComment)
                .join(User, GalleryCommentLike.user_id == User.id)
                .join(GalleryComment, GalleryCommentLike.comment_id == GalleryComment.id)
                .where(
                    and_(
                        GalleryCommentLike.comment_id.in_(my_gallery_comment_ids),
                        GalleryCommentLike.user_id != current_user.id
                    )
                )
                .order_by(desc(GalleryCommentLike.created_at))
                .limit(50)
            )
            result = await db.execute(gallery_comment_likes_query)
            for like, user, comment in result.fetchall():
                is_vip, vip_level = await get_user_vip_info(db, user.id)
                items.append({
                    'id': like.id + 2000000,
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar,
                    'content': (comment.content or '')[:30],
                    'target_id': comment.gallery_id,
                    'target_title': None,
                    'target_type': 'gallery_comment',
                    'notification_type': 'like',
                    'is_vip': is_vip,
                    'vip_level': vip_level,
                    'created_at': like.created_at
                })
        
        # 按时间排序并分页
        items.sort(key=lambda x: x['created_at'], reverse=True)
        total = len(items)
        offset = (page - 1) * page_size
        items = items[offset:offset + page_size]
        
        return NotificationListResponse(
            items=[NotificationItem(**item) for item in items],
            total=total,
            unread_count=0
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取未读通知总数"""
    from app.models.social import MessageConversation
    from datetime import timedelta
    
    private_unread = 0
    comment_unread = 0
    like_unread = 0
    
    # 获取用户最后查看通知的时间（存储在用户表的 last_notification_read 字段）
    # 如果没有，默认为24小时前
    last_read_time = getattr(current_user, 'last_notification_read', None)
    if not last_read_time:
        last_read_time = datetime.utcnow() - timedelta(hours=24)
    
    # 1. 私信未读数
    try:
        conv_query = select(MessageConversation).where(
            or_(
                MessageConversation.user1_id == current_user.id,
                MessageConversation.user2_id == current_user.id
            )
        )
        conv_result = await db.execute(conv_query)
        for conv in conv_result.scalars().all():
            if conv.user1_id == current_user.id:
                private_unread += conv.user1_unread or 0
            else:
                private_unread += conv.user2_unread or 0
    except:
        pass
    
    # 2. 评论未读数 - 统计最后查看时间之后的新评论
    try:
        # 帖子评论
        user_posts_result = await db.execute(
            select(Post.id).where(Post.user_id == current_user.id)
        )
        user_post_ids = [row[0] for row in user_posts_result.fetchall()]
        
        if user_post_ids:
            comment_count_query = select(func.count(PostComment.id)).where(
                and_(
                    PostComment.post_id.in_(user_post_ids),
                    PostComment.user_id != current_user.id,
                    PostComment.status == 'visible',
                    PostComment.created_at > last_read_time
                )
            )
            result = await db.execute(comment_count_query)
            comment_unread += result.scalar() or 0
        
        # 评论回复
        my_comments_result = await db.execute(
            select(PostComment.id).where(PostComment.user_id == current_user.id)
        )
        my_comment_ids = [row[0] for row in my_comments_result.fetchall()]
        
        if my_comment_ids:
            reply_count_query = select(func.count(PostComment.id)).where(
                and_(
                    PostComment.parent_id.in_(my_comment_ids),
                    PostComment.user_id != current_user.id,
                    PostComment.status == 'visible',
                    PostComment.created_at > last_read_time
                )
            )
            result = await db.execute(reply_count_query)
            comment_unread += result.scalar() or 0
    except:
        pass
    
    # 3. 点赞未读数
    try:
        # 帖子点赞
        if user_post_ids:
            like_count_query = select(func.count(PostLike.id)).where(
                and_(
                    PostLike.post_id.in_(user_post_ids),
                    PostLike.user_id != current_user.id,
                    PostLike.created_at > last_read_time
                )
            )
            result = await db.execute(like_count_query)
            like_unread += result.scalar() or 0
        
        # 评论点赞
        if my_comment_ids:
            comment_like_query = select(func.count(PostCommentLike.id)).where(
                and_(
                    PostCommentLike.comment_id.in_(my_comment_ids),
                    PostCommentLike.user_id != current_user.id,
                    PostCommentLike.created_at > last_read_time
                )
            )
            result = await db.execute(comment_like_query)
            like_unread += result.scalar() or 0
    except:
        pass
    
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
    target_user_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """标记通知为已读"""
    from app.models.social import MessageConversation
    
    try:
        if notification_type in ['private', 'all']:
            if target_user_id:
                conv_query = select(MessageConversation).where(
                    or_(
                        and_(MessageConversation.user1_id == current_user.id, MessageConversation.user2_id == target_user_id),
                        and_(MessageConversation.user1_id == target_user_id, MessageConversation.user2_id == current_user.id)
                    )
                )
            else:
                conv_query = select(MessageConversation).where(
                    or_(MessageConversation.user1_id == current_user.id, MessageConversation.user2_id == current_user.id)
                )
            
            conv_result = await db.execute(conv_query)
            for conv in conv_result.scalars().all():
                if conv.user1_id == current_user.id:
                    conv.user1_unread = 0
                else:
                    conv.user2_unread = 0
        
        # 更新用户最后查看通知的时间
        if notification_type in ['comment', 'like', 'all']:
            current_user.last_notification_read = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "已标记为已读"}
    except Exception as e:
        return {"success": False, "message": str(e)}
