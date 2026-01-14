"""排行榜API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.models.video import Video, VideoStatus
from app.models.community import Post, Novel, Gallery

router = APIRouter(prefix="/ranking", tags=["排行榜"])


def get_time_range(time_range: str):
    """获取时间范围"""
    now = datetime.utcnow()
    if time_range == "week":
        return now - timedelta(days=7)
    elif time_range == "month":
        return now - timedelta(days=30)
    elif time_range == "season":
        return now - timedelta(days=90)
    else:  # total
        return None


@router.get("/videos")
async def get_video_ranking(
    time_range: str = Query("week", description="week/month/season/total"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """视频排行榜"""
    query = select(Video).options(
        selectinload(Video.category),
        selectinload(Video.tags)
    ).where(
        Video.status == VideoStatus.PUBLISHED,
        Video.is_short != True
    )
    
    start_time = get_time_range(time_range)
    if start_time:
        query = query.where(Video.created_at >= start_time)
    
    query = query.order_by(desc(Video.view_count), desc(Video.like_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return {
        "items": [
            {
                "id": v.id,
                "title": v.title,
                "cover_url": v.cover_url,
                "duration": v.duration or 0,
                "view_count": v.view_count or 0,
                "like_count": v.like_count or 0,
                "category_name": v.category.name if v.category else None,
                "tags": [t.name for t in v.tags] if v.tags else []
            }
            for v in videos
        ]
    }


@router.get("/shorts")
async def get_short_ranking(
    time_range: str = Query("week", description="week/month/season/total"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """短视频排行榜"""
    query = select(Video).options(
        selectinload(Video.tags)
    ).where(
        Video.status == VideoStatus.PUBLISHED,
        Video.is_short == True
    )
    
    start_time = get_time_range(time_range)
    if start_time:
        query = query.where(Video.created_at >= start_time)
    
    query = query.order_by(desc(Video.view_count), desc(Video.like_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return {
        "items": [
            {
                "id": v.id,
                "title": v.title,
                "cover_url": v.cover_url,
                "duration": v.duration or 0,
                "view_count": v.view_count or 0,
                "like_count": v.like_count or 0,
                "tags": [t.name for t in v.tags] if v.tags else []
            }
            for v in videos
        ]
    }


@router.get("/posts")
async def get_post_ranking(
    time_range: str = Query("week", description="week/month/season/total"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """帖子排行榜"""
    query = select(Post).options(
        selectinload(Post.user)
    ).where(Post.status == "published")
    
    start_time = get_time_range(time_range)
    if start_time:
        query = query.where(Post.created_at >= start_time)
    
    query = query.order_by(desc(Post.view_count), desc(Post.like_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # 获取所有话题ID
    all_topic_ids = set()
    for p in posts:
        if p.topic_ids:
            all_topic_ids.update(p.topic_ids)
    
    # 批量查询话题
    topics_map = {}
    if all_topic_ids:
        from app.models.community import Topic
        topic_result = await db.execute(
            select(Topic).where(Topic.id.in_(all_topic_ids))
        )
        for t in topic_result.scalars().all():
            topics_map[t.id] = {"id": t.id, "name": t.name}
    
    return {
        "items": [
            {
                "id": p.id,
                "title": p.content[:50] if p.content else "",
                "content": p.content,
                "cover_url": p.images[0] if p.images else None,
                "images": p.images or [],
                "view_count": p.view_count or 0,
                "like_count": p.like_count or 0,
                "comment_count": p.comment_count or 0,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "user": {
                    "id": p.user.id,
                    "username": p.user.username,
                    "nickname": p.user.nickname,
                    "avatar": p.user.avatar,
                    "is_vip": getattr(p.user, 'is_vip', False),
                    "vip_level": getattr(p.user, 'vip_level', 0)
                } if p.user else None,
                "topics": [topics_map[tid] for tid in (p.topic_ids or []) if tid in topics_map]
            }
            for p in posts
        ]
    }


@router.get("/novels")
async def get_novel_ranking(
    time_range: str = Query("week", description="week/month/season/total"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """小说排行榜"""
    query = select(Novel).where(Novel.is_active == True)
    
    start_time = get_time_range(time_range)
    if start_time:
        query = query.where(Novel.created_at >= start_time)
    
    query = query.order_by(desc(Novel.view_count), desc(Novel.like_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    novels = result.scalars().all()
    
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "cover": n.cover,
                "cover_url": n.cover,
                "novel_type": n.novel_type,
                "view_count": n.view_count or 0,
                "like_count": n.like_count or 0,
                "tag": n.author or "小说"
            }
            for n in novels
        ]
    }


@router.get("/galleries")
async def get_gallery_ranking(
    time_range: str = Query("week", description="week/month/season/total"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """图集排行榜"""
    query = select(Gallery).where(Gallery.is_active == True)
    
    start_time = get_time_range(time_range)
    if start_time:
        query = query.where(Gallery.created_at >= start_time)
    
    query = query.order_by(desc(Gallery.view_count), desc(Gallery.like_count))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    galleries = result.scalars().all()
    
    return {
        "items": [
            {
                "id": g.id,
                "title": g.title,
                "cover": g.cover,
                "cover_url": g.cover,
                "view_count": g.view_count or 0,
                "like_count": g.like_count or 0,
                "tag": "图集"
            }
            for g in galleries
        ]
    }
