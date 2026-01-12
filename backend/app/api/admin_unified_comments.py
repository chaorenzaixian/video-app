"""
统一评论管理 API
管理所有类型的评论：长视频、短视频、社区帖子、图集、小�?
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.admin import get_admin_user
from app.models.user import User
from app.models.comment import Comment
from app.models.community import PostComment, GalleryComment, NovelComment
from app.models.video import Video

router = APIRouter(prefix="/admin/unified-comments", tags=["统一评论管理"])


class CommentItem(BaseModel):
    id: int
    type: str


class BatchRequest(BaseModel):
    items: List[CommentItem]


class UpdateCommentRequest(BaseModel):
    is_hidden: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_official: Optional[bool] = None


@router.get("/stats")
async def get_comment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取各类型评论统�?""
    try:
        # 长视频评论数
        video_result = await db.execute(
            select(func.count(Comment.id))
            .join(Video, Comment.video_id == Video.id)
            .where(Video.is_short == False)
        )
        video_count = video_result.scalar() or 0
        
        # 短视频评论数
        short_result = await db.execute(
            select(func.count(Comment.id))
            .join(Video, Comment.video_id == Video.id)
            .where(Video.is_short == True)
        )
        short_count = short_result.scalar() or 0
        
        # 社区帖子评论�?
        post_result = await db.execute(select(func.count(PostComment.id)))
        post_count = post_result.scalar() or 0
        
        # 图集评论�?
        gallery_result = await db.execute(select(func.count(GalleryComment.id)))
        gallery_count = gallery_result.scalar() or 0
        
        # 小说评论�?
        novel_result = await db.execute(select(func.count(NovelComment.id)))
        novel_count = novel_result.scalar() or 0
        
        total = video_count + short_count + post_count + gallery_count + novel_count
        
        return {
            "all": total,
            "video": video_count,
            "short": short_count,
            "post": post_count,
            "gallery": gallery_count,
            "novel": novel_count
        }
    except Exception as e:
        print(f"获取评论统计失败: {e}")
        return {"all": 0, "video": 0, "short": 0, "post": 0, "gallery": 0, "novel": 0}


@router.get("")
async def get_unified_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: str = Query("", description="评论类型: video/short/post/gallery/novel"),
    keyword: str = Query("", description="搜索关键�?),
    status: str = Query("", description="状�? visible/hidden"),
    start_date: str = Query("", description="开始日�?),
    end_date: str = Query("", description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """获取统一评论列表"""
    all_comments = []
    
    # 解析日期
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    # 根据类型查询
    types_to_query = []
    if not content_type or content_type == "all":
        types_to_query = ["video", "short", "post", "gallery", "novel"]
    else:
        types_to_query = [content_type]
    
    # 查询长视�?短视频评�?
    if "video" in types_to_query or "short" in types_to_query:
        query = (
            select(Comment, User, Video)
            .outerjoin(User, Comment.user_id == User.id)
            .join(Video, Comment.video_id == Video.id)
        )
        
        conditions = []
        if "video" in types_to_query and "short" not in types_to_query:
            conditions.append(Video.is_short == False)
        elif "short" in types_to_query and "video" not in types_to_query:
            conditions.append(Video.is_short == True)
        
        if keyword:
            conditions.append(or_(
                Comment.content.ilike(f"%{keyword}%"),
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%")
            ))
        if status == "visible":
            conditions.append(Comment.is_hidden == False)
        elif status == "hidden":
            conditions.append(Comment.is_hidden == True)
        if start_dt:
            conditions.append(Comment.created_at >= start_dt)
        if end_dt:
            conditions.append(Comment.created_at <= end_dt)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query.order_by(Comment.created_at.desc()))
        for comment, user, video in result.fetchall():
            all_comments.append({
                "id": comment.id,
                "content_type": "short" if video.is_short else "video",
                "content_id": comment.video_id,
                "content": comment.content,
                "user_id": comment.user_id,
                "user_name": user.nickname or user.username if user else "未知用户",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.is_hidden or False,
                "is_pinned": comment.is_pinned or False,
                "is_official": getattr(comment, 'is_official', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # 查询社区帖子评论
    if "post" in types_to_query:
        query = (
            select(PostComment, User)
            .outerjoin(User, PostComment.user_id == User.id)
        )
        
        conditions = []
        if keyword:
            conditions.append(or_(
                PostComment.content.ilike(f"%{keyword}%"),
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%")
            ))
        if status == "visible":
            conditions.append(PostComment.status == "visible")
        elif status == "hidden":
            conditions.append(PostComment.status == "hidden")
        if start_dt:
            conditions.append(PostComment.created_at >= start_dt)
        if end_dt:
            conditions.append(PostComment.created_at <= end_dt)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query.order_by(PostComment.created_at.desc()))
        for comment, user in result.fetchall():
            all_comments.append({
                "id": comment.id,
                "content_type": "post",
                "content_id": comment.post_id,
                "content": comment.content,
                "user_id": comment.user_id,
                "user_name": user.nickname or user.username if user else "未知用户",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.status == "hidden",
                "is_pinned": getattr(comment, 'is_pinned', False),
                "is_official": getattr(comment, 'is_official', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # 查询图集评论
    if "gallery" in types_to_query:
        query = (
            select(GalleryComment, User)
            .outerjoin(User, GalleryComment.user_id == User.id)
        )
        
        conditions = []
        if keyword:
            conditions.append(or_(
                GalleryComment.content.ilike(f"%{keyword}%"),
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%")
            ))
        if status == "visible":
            conditions.append(GalleryComment.status == "visible")
        elif status == "hidden":
            conditions.append(GalleryComment.status == "hidden")
        if start_dt:
            conditions.append(GalleryComment.created_at >= start_dt)
        if end_dt:
            conditions.append(GalleryComment.created_at <= end_dt)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query.order_by(GalleryComment.created_at.desc()))
        for comment, user in result.fetchall():
            all_comments.append({
                "id": comment.id,
                "content_type": "gallery",
                "content_id": comment.gallery_id,
                "content": comment.content,
                "user_id": comment.user_id,
                "user_name": user.nickname or user.username if user else "未知用户",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.status == "hidden",
                "is_pinned": getattr(comment, 'is_pinned', False),
                "is_official": getattr(comment, 'is_official', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # 查询小说评论
    if "novel" in types_to_query:
        query = (
            select(NovelComment, User)
            .outerjoin(User, NovelComment.user_id == User.id)
        )
        
        conditions = []
        if keyword:
            conditions.append(or_(
                NovelComment.content.ilike(f"%{keyword}%"),
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%")
            ))
        if status == "visible":
            conditions.append(NovelComment.status == "visible")
        elif status == "hidden":
            conditions.append(NovelComment.status == "hidden")
        if start_dt:
            conditions.append(NovelComment.created_at >= start_dt)
        if end_dt:
            conditions.append(NovelComment.created_at <= end_dt)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query.order_by(NovelComment.created_at.desc()))
        for comment, user in result.fetchall():
            all_comments.append({
                "id": comment.id,
                "content_type": "novel",
                "content_id": comment.novel_id,
                "content": comment.content,
                "user_id": comment.user_id,
                "user_name": user.nickname or user.username if user else "未知用户",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.status == "hidden",
                "is_pinned": getattr(comment, 'is_pinned', False),
                "is_official": getattr(comment, 'is_official', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # 按时间排�?
    all_comments.sort(key=lambda x: x["created_at"] or "", reverse=True)
    
    # 分页
    total = len(all_comments)
    start = (page - 1) * page_size
    end = start + page_size
    items = all_comments[start:end]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.put("/{content_type}/{comment_id}")
async def update_comment(
    content_type: str,
    comment_id: int,
    data: UpdateCommentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """更新评论状�?""
    try:
        if content_type in ["video", "short"]:
            stmt = update(Comment).where(Comment.id == comment_id)
            update_data = {}
            if data.is_hidden is not None:
                update_data["is_hidden"] = data.is_hidden
            if data.is_pinned is not None:
                update_data["is_pinned"] = data.is_pinned
            if data.is_official is not None:
                update_data["is_official"] = data.is_official
            if update_data:
                await db.execute(stmt.values(**update_data))
        
        elif content_type == "post":
            stmt = update(PostComment).where(PostComment.id == comment_id)
            update_data = {}
            if data.is_hidden is not None:
                update_data["status"] = "hidden" if data.is_hidden else "visible"
            if update_data:
                await db.execute(stmt.values(**update_data))
        
        elif content_type == "gallery":
            stmt = update(GalleryComment).where(GalleryComment.id == comment_id)
            update_data = {}
            if data.is_hidden is not None:
                update_data["status"] = "hidden" if data.is_hidden else "visible"
            if update_data:
                await db.execute(stmt.values(**update_data))
        
        elif content_type == "novel":
            stmt = update(NovelComment).where(NovelComment.id == comment_id)
            update_data = {}
            if data.is_hidden is not None:
                update_data["status"] = "hidden" if data.is_hidden else "visible"
            if update_data:
                await db.execute(stmt.values(**update_data))
        
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{content_type}/{comment_id}")
async def delete_comment(
    content_type: str,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """删除评论"""
    try:
        if content_type in ["video", "short"]:
            await db.execute(delete(Comment).where(Comment.id == comment_id))
        elif content_type == "post":
            await db.execute(delete(PostComment).where(PostComment.id == comment_id))
        elif content_type == "gallery":
            await db.execute(delete(GalleryComment).where(GalleryComment.id == comment_id))
        elif content_type == "novel":
            await db.execute(delete(NovelComment).where(NovelComment.id == comment_id))
        
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-delete")
async def batch_delete_comments(
    data: BatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量删除评论"""
    try:
        for item in data.items:
            if item.type in ["video", "short"]:
                await db.execute(delete(Comment).where(Comment.id == item.id))
            elif item.type == "post":
                await db.execute(delete(PostComment).where(PostComment.id == item.id))
            elif item.type == "gallery":
                await db.execute(delete(GalleryComment).where(GalleryComment.id == item.id))
            elif item.type == "novel":
                await db.execute(delete(NovelComment).where(NovelComment.id == item.id))
        
        await db.commit()
        return {"success": True, "deleted": len(data.items)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-hide")
async def batch_hide_comments(
    data: BatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """批量隐藏评论"""
    try:
        for item in data.items:
            if item.type in ["video", "short"]:
                await db.execute(
                    update(Comment).where(Comment.id == item.id).values(is_hidden=True)
                )
            elif item.type == "post":
                await db.execute(
                    update(PostComment).where(PostComment.id == item.id).values(status="hidden")
                )
            elif item.type == "gallery":
                await db.execute(
                    update(GalleryComment).where(GalleryComment.id == item.id).values(status="hidden")
                )
            elif item.type == "novel":
                await db.execute(
                    update(NovelComment).where(NovelComment.id == item.id).values(status="hidden")
                )
        
        await db.commit()
        return {"success": True, "hidden": len(data.items)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
