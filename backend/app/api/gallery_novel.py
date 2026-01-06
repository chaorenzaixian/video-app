"""
图集和小说API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.models.community import (
    GalleryCategory, Gallery, 
    NovelCategory, Novel, NovelChapter
)

router = APIRouter(prefix="/gallery-novel", tags=["图集小说"])


# ========== 图集API ==========

@router.get("/gallery/categories")
async def get_gallery_categories(db: AsyncSession = Depends(get_db)):
    """获取图集分类"""
    result = await db.execute(
        select(GalleryCategory)
        .where(GalleryCategory.is_active == True)
        .order_by(desc(GalleryCategory.sort_order), GalleryCategory.id)
    )
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in categories]


@router.get("/gallery/list")
async def get_gallery_list(
    category_id: Optional[int] = None,
    sort: str = Query("hot", description="hot/new/views"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取图集列表"""
    query = select(Gallery).where(Gallery.is_active == True)
    
    if category_id:
        query = query.where(Gallery.category_id == category_id)
    
    if sort == "new":
        query = query.order_by(desc(Gallery.created_at))
    elif sort == "views":
        query = query.order_by(desc(Gallery.view_count))
    else:  # hot
        query = query.order_by(desc(Gallery.is_hot), desc(Gallery.like_count), desc(Gallery.created_at))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    galleries = result.scalars().all()
    
    return [
        {
            "id": g.id,
            "title": g.title,
            "cover": g.cover,
            "view_count": g.view_count,
            "image_count": g.image_count,
            "chapter_count": g.chapter_count,
            "status": "连载中" if g.status == "ongoing" else "已完结"
        }
        for g in galleries
    ]


@router.get("/gallery/{gallery_id}")
async def get_gallery_detail(
    gallery_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取图集详情"""
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    
    if not gallery or not gallery.is_active:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    # 增加浏览量
    gallery.view_count += 1
    await db.commit()
    
    return {
        "id": gallery.id,
        "title": gallery.title,
        "cover": gallery.cover,
        "images": gallery.images or [],
        "description": gallery.description,
        "view_count": gallery.view_count,
        "like_count": gallery.like_count,
        "image_count": gallery.image_count,
        "chapter_count": gallery.chapter_count,
        "status": gallery.status
    }


# ========== 小说API ==========

@router.get("/novel/categories")
async def get_novel_categories(
    novel_type: str = Query("text", description="text/audio"),
    db: AsyncSession = Depends(get_db)
):
    """获取小说分类"""
    result = await db.execute(
        select(NovelCategory)
        .where(NovelCategory.is_active == True, NovelCategory.novel_type == novel_type)
        .order_by(desc(NovelCategory.sort_order), NovelCategory.id)
    )
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in categories]


@router.get("/novel/list")
async def get_novel_list(
    category_id: Optional[int] = None,
    novel_type: str = Query("text", description="text/audio"),
    sort: str = Query("hot", description="hot/new/views"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取小说列表"""
    query = select(Novel).where(Novel.is_active == True, Novel.novel_type == novel_type)
    
    if category_id:
        query = query.where(Novel.category_id == category_id)
    
    if sort == "new":
        query = query.order_by(desc(Novel.created_at))
    elif sort == "views":
        query = query.order_by(desc(Novel.view_count))
    else:  # hot
        query = query.order_by(desc(Novel.is_hot), desc(Novel.like_count), desc(Novel.created_at))
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    novels = result.scalars().all()
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "author": n.author,
            "cover": n.cover,
            "view_count": n.view_count,
            "chapter_count": n.chapter_count,
            "status": "连载中" if n.status == "ongoing" else "已完结"
        }
        for n in novels
    ]


@router.get("/novel/{novel_id}")
async def get_novel_detail(
    novel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取小说详情"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    
    if not novel or not novel.is_active:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 增加浏览量
    novel.view_count += 1
    await db.commit()
    
    # 获取章节列表
    chapters_result = await db.execute(
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_num)
    )
    chapters = chapters_result.scalars().all()
    
    return {
        "id": novel.id,
        "title": novel.title,
        "author": novel.author,
        "cover": novel.cover,
        "description": novel.description,
        "novel_type": novel.novel_type,
        "view_count": novel.view_count,
        "like_count": novel.like_count,
        "chapter_count": novel.chapter_count,
        "status": novel.status,
        "chapters": [
            {"id": c.id, "num": c.chapter_num, "title": c.title, "is_free": c.is_free}
            for c in chapters
        ]
    }


@router.get("/novel/{novel_id}/chapter/{chapter_id}")
async def get_novel_chapter(
    novel_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取小说章节内容"""
    result = await db.execute(
        select(NovelChapter).where(
            NovelChapter.id == chapter_id,
            NovelChapter.novel_id == novel_id
        )
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    return {
        "id": chapter.id,
        "novel_id": chapter.novel_id,
        "chapter_num": chapter.chapter_num,
        "title": chapter.title,
        "content": chapter.content,
        "audio_url": chapter.audio_url,
        "is_free": chapter.is_free
    }
