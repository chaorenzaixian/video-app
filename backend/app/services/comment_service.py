"""
评论公共服务层
提取 comments.py 和 admin_unified_comments.py 的公共逻辑
"""
from typing import Optional, List, Dict, Set, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.user import User, UserVIP
from app.models.comment import Comment, CommentLike
from app.models.video import Video
from app.schemas.comment import CommentResponse


class CommentService:
    """评论服务 - 提供评论相关的公共方法"""
    
    # ========== 批量查询方法 ==========
    
    @staticmethod
    async def batch_get_user_vip_levels(
        db: AsyncSession, 
        user_ids: List[int]
    ) -> Dict[int, int]:
        """
        批量获取用户VIP等级
        
        Args:
            db: 数据库会话
            user_ids: 用户ID列表
            
        Returns:
            Dict[user_id, vip_level]
        """
        if not user_ids:
            return {}
        
        result = await db.execute(
            select(UserVIP).where(UserVIP.user_id.in_(user_ids))
        )
        vips = result.scalars().all()
        
        vip_map = {}
        now = datetime.utcnow()
        for vip in vips:
            if vip.is_active and vip.expire_date and vip.expire_date > now:
                vip_map[vip.user_id] = getattr(vip, 'vip_level', 0) or 0
        
        # 未找到的用户VIP等级为0
        for uid in user_ids:
            if uid not in vip_map:
                vip_map[uid] = 0
        
        return vip_map
    
    @staticmethod
    async def batch_get_liked_comment_ids(
        db: AsyncSession, 
        comment_ids: List[int], 
        user_id: int
    ) -> Set[int]:
        """
        批量获取用户点赞的评论ID
        
        Args:
            db: 数据库会话
            comment_ids: 评论ID列表
            user_id: 用户ID
            
        Returns:
            Set[comment_id] - 用户点赞的评论ID集合
        """
        if not comment_ids or not user_id:
            return set()
        
        result = await db.execute(
            select(CommentLike.comment_id).where(
                CommentLike.comment_id.in_(comment_ids),
                CommentLike.user_id == user_id
            )
        )
        return set(row[0] for row in result.all())
    
    @staticmethod
    async def check_user_is_vip(db: AsyncSession, user_id: int) -> bool:
        """检查用户是否是VIP"""
        result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == user_id)
        )
        vip = result.scalar_one_or_none()
        if vip and vip.is_active and vip.expire_date:
            return vip.expire_date > datetime.utcnow()
        return False
    
    @staticmethod
    async def get_user_vip_level(db: AsyncSession, user_id: int) -> int:
        """获取单个用户的VIP等级"""
        vip_map = await CommentService.batch_get_user_vip_levels(db, [user_id])
        return vip_map.get(user_id, 0)
    
    # ========== 响应构建方法 ==========
    
    @staticmethod
    def build_comment_response(
        comment: Comment,
        user: User,
        vip_level: int,
        is_liked: bool,
        replies: List[CommentResponse] = None
    ) -> CommentResponse:
        """
        构建评论响应对象
        
        Args:
            comment: 评论对象
            user: 用户对象
            vip_level: VIP等级
            is_liked: 是否已点赞
            replies: 回复列表
            
        Returns:
            CommentResponse
        """
        return CommentResponse(
            id=comment.id,
            content=comment.content,
            image_url=comment.image_url,
            video_id=comment.video_id,
            user_id=comment.user_id,
            user_name=user.nickname or user.username if user else "Unknown",
            user_avatar=user.avatar if user else None,
            user_vip_level=vip_level,
            parent_id=comment.parent_id,
            like_count=comment.like_count or 0,
            reply_count=comment.reply_count or 0,
            is_pinned=comment.is_pinned or False,
            is_official=getattr(comment, 'is_official', False),
            is_god=getattr(comment, 'is_god', False),
            is_liked=is_liked,
            created_at=comment.created_at,
            replies=replies or []
        )
    
    @staticmethod
    def build_comment_dict(
        comment: Any,
        user: Optional[User],
        content_type: str,
        content_id: int
    ) -> Dict:
        """
        构建评论字典（用于管理后台）
        
        Args:
            comment: 评论对象（可以是不同类型）
            user: 用户对象
            content_type: 内容类型
            content_id: 内容ID
            
        Returns:
            评论字典
        """
        # 处理不同评论类型的隐藏状态
        is_hidden = False
        if hasattr(comment, 'is_hidden'):
            is_hidden = comment.is_hidden or False
        elif hasattr(comment, 'status'):
            is_hidden = comment.status == "hidden"
        
        return {
            "id": comment.id,
            "content_type": content_type,
            "content_id": content_id,
            "content": comment.content,
            "user_id": comment.user_id,
            "user_name": user.nickname or user.username if user else "Unknown",
            "user_avatar": user.avatar if user else None,
            "parent_id": getattr(comment, 'parent_id', None),
            "like_count": getattr(comment, 'like_count', 0) or 0,
            "reply_count": getattr(comment, 'reply_count', 0) or 0,
            "is_hidden": is_hidden,
            "is_pinned": getattr(comment, 'is_pinned', False) or False,
            "is_official": getattr(comment, 'is_official', False) or False,
            "is_god": getattr(comment, 'is_god', False) or False,
            "created_at": comment.created_at.isoformat() if comment.created_at else None
        }
    
    # ========== 评论查询方法 ==========
    
    @staticmethod
    async def get_video_comments(
        db: AsyncSession,
        video_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "newest",
        current_user_id: Optional[int] = None
    ) -> Dict:
        """
        获取视频评论列表（优化版）
        
        Args:
            db: 数据库会话
            video_id: 视频ID
            page: 页码
            page_size: 每页数量
            sort_by: 排序方式 (newest/hottest)
            current_user_id: 当前用户ID（用于判断点赞状态）
            
        Returns:
            {"items": [...], "total": int, "page": int, "page_size": int}
        """
        from sqlalchemy import desc
        
        # 基础查询：只获取顶级评论，预加载用户关系
        query = select(Comment).where(
            Comment.video_id == video_id,
            Comment.parent_id == None,
            Comment.is_hidden == False
        ).options(selectinload(Comment.user))
        
        # 统计总数
        count_query = select(func.count()).select_from(
            select(Comment.id).where(
                Comment.video_id == video_id,
                Comment.parent_id == None,
                Comment.is_hidden == False
            ).subquery()
        )
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 排序
        if sort_by == "hottest":
            query = query.order_by(
                desc(Comment.is_pinned), 
                desc(Comment.like_count), 
                desc(Comment.created_at)
            )
        else:
            query = query.order_by(
                desc(Comment.is_pinned), 
                desc(Comment.created_at)
            )
        
        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        comments = result.scalars().all()
        
        if not comments:
            return {"items": [], "total": total, "page": page, "page_size": page_size}
        
        # 收集所有需要查询的用户ID和评论ID
        user_ids = set(c.user_id for c in comments)
        comment_ids = [c.id for c in comments]
        
        # 获取有回复的评论的回复（限制3条）
        reply_map: Dict[int, List[Comment]] = {}
        comments_with_replies = [c for c in comments if c.reply_count > 0]
        
        if comments_with_replies:
            for parent_id in [c.id for c in comments_with_replies]:
                reply_result = await db.execute(
                    select(Comment)
                    .where(Comment.parent_id == parent_id, Comment.is_hidden == False)
                    .options(selectinload(Comment.user))
                    .order_by(Comment.created_at)
                    .limit(3)
                )
                replies = reply_result.scalars().all()
                reply_map[parent_id] = replies
                for r in replies:
                    user_ids.add(r.user_id)
                    comment_ids.append(r.id)
        
        # 批量查询VIP等级
        vip_map = await CommentService.batch_get_user_vip_levels(db, list(user_ids))
        
        # 批量查询点赞状态
        liked_ids = set()
        if current_user_id:
            liked_ids = await CommentService.batch_get_liked_comment_ids(
                db, comment_ids, current_user_id
            )
        
        # 构建响应
        items = []
        for comment in comments:
            replies_response = []
            if comment.id in reply_map:
                for reply in reply_map[comment.id]:
                    replies_response.append(CommentService.build_comment_response(
                        comment=reply,
                        user=reply.user,
                        vip_level=vip_map.get(reply.user_id, 0),
                        is_liked=reply.id in liked_ids
                    ))
            
            items.append(CommentService.build_comment_response(
                comment=comment,
                user=comment.user,
                vip_level=vip_map.get(comment.user_id, 0),
                is_liked=comment.id in liked_ids,
                replies=replies_response
            ))
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    # ========== 评论操作方法 ==========
    
    @staticmethod
    async def toggle_like(
        db: AsyncSession,
        comment_id: int,
        user_id: int
    ) -> Dict:
        """
        切换评论点赞状态
        
        Returns:
            {"liked": bool, "like_count": int, "message": str}
        """
        result = await db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise ValueError("评论不存在")
        
        # 检查是否已点赞
        like_result = await db.execute(
            select(CommentLike).where(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == user_id
            )
        )
        existing_like = like_result.scalar_one_or_none()
        
        if existing_like:
            await db.delete(existing_like)
            comment.like_count = max(0, comment.like_count - 1)
            liked = False
            message = "已取消点赞"
        else:
            like = CommentLike(comment_id=comment_id, user_id=user_id)
            db.add(like)
            comment.like_count += 1
            liked = True
            message = "点赞成功"
        
        await db.commit()
        
        return {
            "liked": liked,
            "like_count": comment.like_count,
            "message": message
        }
    
    @staticmethod
    async def soft_delete_comment(
        db: AsyncSession,
        comment_id: int
    ) -> bool:
        """
        软删除评论
        
        Returns:
            是否成功
        """
        result = await db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            return False
        
        comment.is_hidden = True
        
        # 更新视频评论数
        if comment.video_id:
            video_result = await db.execute(
                select(Video).where(Video.id == comment.video_id)
            )
            video = video_result.scalar_one_or_none()
            if video:
                video.comment_count = max(0, video.comment_count - 1)
        
        await db.commit()
        return True
