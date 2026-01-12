# -*- coding: utf-8 -*-
"""
Unified Comments Management API
Manage all types of comments: videos, short videos, community posts, galleries, novels
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.admin import get_admin_user
from app.models.user import User
from app.models.comment import Comment
from app.models.community import PostComment, GalleryComment, NovelComment
from app.models.video import Video

router = APIRouter(prefix="/admin/unified-comments", tags=["Unified Comments"])


class CommentItem(BaseModel):
    id: int
    type: str


class BatchRequest(BaseModel):
    items: List[CommentItem]


class UpdateCommentRequest(BaseModel):
    is_hidden: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_official: Optional[bool] = None
    is_god: Optional[bool] = None


@router.get("/stats")
async def get_comment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get comment statistics by type"""
    try:
        video_result = await db.execute(
            select(func.count(Comment.id))
            .join(Video, Comment.video_id == Video.id)
            .where(Video.is_short == False)
        )
        video_count = video_result.scalar() or 0
        
        short_result = await db.execute(
            select(func.count(Comment.id))
            .join(Video, Comment.video_id == Video.id)
            .where(Video.is_short == True)
        )
        short_count = short_result.scalar() or 0
        
        post_result = await db.execute(select(func.count(PostComment.id)))
        post_count = post_result.scalar() or 0
        
        gallery_result = await db.execute(select(func.count(GalleryComment.id)))
        gallery_count = gallery_result.scalar() or 0
        
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
        print(f"Failed to get comment stats: {e}")
        return {"all": 0, "video": 0, "short": 0, "post": 0, "gallery": 0, "novel": 0}


@router.get("")
async def get_unified_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    content_type: str = Query("", description="Comment type: video/short/post/gallery/novel"),
    keyword: str = Query("", description="Search keyword"),
    status: str = Query("", description="Status: visible/hidden"),
    start_date: str = Query("", description="Start date"),
    end_date: str = Query("", description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Get unified comments list"""
    all_comments = []
    
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
    
    types_to_query = []
    if not content_type or content_type == "all":
        types_to_query = ["video", "short", "post", "gallery", "novel"]
    else:
        types_to_query = [content_type]
    
    # Query video/short video comments
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
                "user_name": user.nickname or user.username if user else "Unknown",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.is_hidden or False,
                "is_pinned": comment.is_pinned or False,
                "is_official": getattr(comment, 'is_official', False),
                "is_god": getattr(comment, 'is_god', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # Query post comments
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
                "user_name": user.nickname or user.username if user else "Unknown",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.status == "hidden",
                "is_pinned": getattr(comment, 'is_pinned', False),
                "is_official": getattr(comment, 'is_official', False),
                "is_god": getattr(comment, 'is_god', False),
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # Query gallery comments
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
            conditions.append(GalleryComment.is_hidden == False)
        elif status == "hidden":
            conditions.append(GalleryComment.is_hidden == True)
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
                "user_name": user.nickname or user.username if user else "Unknown",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.is_hidden or False,
                "is_pinned": comment.is_pinned or False,
                "is_official": comment.is_official or False,
                "is_god": comment.is_god or False,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # Query novel comments
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
            conditions.append(NovelComment.is_hidden == False)
        elif status == "hidden":
            conditions.append(NovelComment.is_hidden == True)
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
                "user_name": user.nickname or user.username if user else "Unknown",
                "user_avatar": user.avatar if user else None,
                "parent_id": comment.parent_id,
                "like_count": comment.like_count or 0,
                "reply_count": comment.reply_count or 0,
                "is_hidden": comment.is_hidden or False,
                "is_pinned": comment.is_pinned or False,
                "is_official": comment.is_official or False,
                "is_god": comment.is_god or False,
                "created_at": comment.created_at.isoformat() if comment.created_at else None
            })
    
    # Sort by time
    all_comments.sort(key=lambda x: x["created_at"] or "", reverse=True)
    
    # Pagination
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
    update_data: UpdateCommentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Update comment status (hide/show, pin, official, god)"""
    if content_type == "video" or content_type == "short":
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if update_data.is_hidden is not None:
            comment.is_hidden = update_data.is_hidden
        if update_data.is_pinned is not None:
            comment.is_pinned = update_data.is_pinned
        if update_data.is_official is not None:
            comment.is_official = update_data.is_official
        if update_data.is_god is not None:
            comment.is_god = update_data.is_god
    
    elif content_type == "post":
        result = await db.execute(select(PostComment).where(PostComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if update_data.is_hidden is not None:
            comment.status = "hidden" if update_data.is_hidden else "visible"
        if update_data.is_pinned is not None and hasattr(comment, 'is_pinned'):
            comment.is_pinned = update_data.is_pinned
        if update_data.is_official is not None and hasattr(comment, 'is_official'):
            comment.is_official = update_data.is_official
        if update_data.is_god is not None:
            comment.is_god = update_data.is_god
    
    elif content_type == "gallery":
        result = await db.execute(select(GalleryComment).where(GalleryComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if update_data.is_hidden is not None:
            comment.is_hidden = update_data.is_hidden
        if update_data.is_pinned is not None:
            comment.is_pinned = update_data.is_pinned
        if update_data.is_official is not None:
            comment.is_official = update_data.is_official
        if update_data.is_god is not None:
            comment.is_god = update_data.is_god
    
    elif content_type == "novel":
        result = await db.execute(select(NovelComment).where(NovelComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        if update_data.is_hidden is not None:
            comment.is_hidden = update_data.is_hidden
        if update_data.is_pinned is not None:
            comment.is_pinned = update_data.is_pinned
        if update_data.is_official is not None:
            comment.is_official = update_data.is_official
        if update_data.is_god is not None:
            comment.is_god = update_data.is_god
    
    else:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    await db.commit()
    return {"message": "Comment updated successfully"}


@router.delete("/{content_type}/{comment_id}")
async def delete_comment(
    content_type: str,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Delete a comment"""
    if content_type == "video" or content_type == "short":
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        await db.delete(comment)
    
    elif content_type == "post":
        result = await db.execute(select(PostComment).where(PostComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        await db.delete(comment)
    
    elif content_type == "gallery":
        result = await db.execute(select(GalleryComment).where(GalleryComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        await db.delete(comment)
    
    elif content_type == "novel":
        result = await db.execute(select(NovelComment).where(NovelComment.id == comment_id))
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        await db.delete(comment)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    await db.commit()
    return {"message": "Comment deleted successfully"}


@router.post("/batch-delete")
async def batch_delete_comments(
    request: BatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Batch delete comments"""
    deleted_count = 0
    
    for item in request.items:
        try:
            if item.type == "video" or item.type == "short":
                result = await db.execute(select(Comment).where(Comment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    await db.delete(comment)
                    deleted_count += 1
            
            elif item.type == "post":
                result = await db.execute(select(PostComment).where(PostComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    await db.delete(comment)
                    deleted_count += 1
            
            elif item.type == "gallery":
                result = await db.execute(select(GalleryComment).where(GalleryComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    await db.delete(comment)
                    deleted_count += 1
            
            elif item.type == "novel":
                result = await db.execute(select(NovelComment).where(NovelComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    await db.delete(comment)
                    deleted_count += 1
        except Exception as e:
            print(f"Failed to delete comment {item.type}/{item.id}: {e}")
    
    await db.commit()
    return {"message": f"Deleted {deleted_count} comments", "deleted_count": deleted_count}


@router.post("/batch-hide")
async def batch_hide_comments(
    request: BatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Batch hide comments"""
    hidden_count = 0
    
    for item in request.items:
        try:
            if item.type == "video" or item.type == "short":
                result = await db.execute(select(Comment).where(Comment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    comment.is_hidden = True
                    hidden_count += 1
            
            elif item.type == "post":
                result = await db.execute(select(PostComment).where(PostComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    comment.status = "hidden"
                    hidden_count += 1
            
            elif item.type == "gallery":
                result = await db.execute(select(GalleryComment).where(GalleryComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    comment.is_hidden = True
                    hidden_count += 1
            
            elif item.type == "novel":
                result = await db.execute(select(NovelComment).where(NovelComment.id == item.id))
                comment = result.scalar_one_or_none()
                if comment:
                    comment.is_hidden = True
                    hidden_count += 1
        except Exception as e:
            print(f"Failed to hide comment {item.type}/{item.id}: {e}")
    
    await db.commit()
    return {"message": f"Hidden {hidden_count} comments", "hidden_count": hidden_count}
