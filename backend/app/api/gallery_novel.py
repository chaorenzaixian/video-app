"""
图集和小说API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile, Request
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
    search: Optional[str] = None,
    sort: str = Query("hot", description="hot/new/views"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取图集列表"""
    query = select(Gallery).where(Gallery.is_active == True)
    
    if category_id:
        query = query.where(Gallery.category_id == category_id)
    
    # 搜索
    if search:
        query = query.where(Gallery.title.ilike(f"%{search}%"))
    
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
    current_user: Optional[User] = Depends(get_current_user_optional),
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
    
    # 检查用户是否是VIP
    is_vip = False
    if current_user:
        from app.models.user import UserVIP
        from datetime import datetime
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        vip = vip_result.scalar_one_or_none()
        if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
            is_vip = True
        print(f"[DEBUG] user_id={current_user.id}, vip={vip}, is_vip={is_vip}")
    else:
        print(f"[DEBUG] No current_user, is_vip=False")
    
    # 非VIP只返回前5张图片
    all_images = gallery.images or []
    if is_vip:
        display_images = all_images
    else:
        display_images = all_images[:5]  # 非会员只能看5张
    
    # 检查用户点赞和收藏状态
    is_liked = False
    is_collected = False
    if current_user:
        from app.models.community import GalleryLike, GalleryCollect
        like_result = await db.execute(
            select(GalleryLike).where(
                GalleryLike.gallery_id == gallery_id,
                GalleryLike.user_id == current_user.id
            )
        )
        is_liked = like_result.scalar_one_or_none() is not None
        
        collect_result = await db.execute(
            select(GalleryCollect).where(
                GalleryCollect.gallery_id == gallery_id,
                GalleryCollect.user_id == current_user.id
            )
        )
        is_collected = collect_result.scalar_one_or_none() is not None
    
    return {
        "id": gallery.id,
        "title": gallery.title,
        "cover": gallery.cover,
        "images": display_images,
        "description": gallery.description,
        "view_count": gallery.view_count,
        "like_count": gallery.like_count or 0,
        "comment_count": gallery.comment_count or 0,
        "collect_count": gallery.collect_count or 0,
        "image_count": len(all_images),
        "chapter_count": gallery.chapter_count,
        "status": gallery.status,
        "is_vip": is_vip,
        "is_liked": is_liked,
        "is_collected": is_collected
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
    search: Optional[str] = None,
    novel_type: str = Query("all", description="text/audio/all"),
    sort: str = Query("hot", description="hot/new/views"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取小说列表"""
    query = select(Novel).where(Novel.is_active == True)
    
    # 如果有搜索词，不限制类型
    if search:
        query = query.where(Novel.title.ilike(f"%{search}%"))
    elif novel_type != "all":
        query = query.where(Novel.novel_type == novel_type)
    
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
    
    # 获取用户阅读进度
    progress_map = {}
    if current_user:
        from app.models.community import NovelReadProgress
        novel_ids = [n.id for n in novels]
        if novel_ids:
            progress_result = await db.execute(
                select(NovelReadProgress).where(
                    NovelReadProgress.user_id == current_user.id,
                    NovelReadProgress.novel_id.in_(novel_ids)
                )
            )
            for p in progress_result.scalars().all():
                progress_map[p.novel_id] = p.chapter_num
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "author": n.author,
            "cover": n.cover,
            "novel_type": n.novel_type,
            "view_count": n.view_count,
            "chapter_count": n.chapter_count,
            "status": "连载中" if n.status == "ongoing" else "已完结",
            "read_chapter": progress_map.get(n.id, 0)  # 已读到第几章
        }
        for n in novels
    ]


@router.get("/novel/{novel_id}")
async def get_novel_detail(
    novel_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
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
    
    # 检查用户是否是VIP
    is_vip = False
    if current_user:
        from app.models.user import UserVIP
        vip_result = await db.execute(
            select(UserVIP).where(UserVIP.user_id == current_user.id)
        )
        vip = vip_result.scalar_one_or_none()
        if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
            is_vip = True
    
    # 获取阅读进度
    read_progress = None
    if current_user:
        from app.models.community import NovelReadProgress
        progress_result = await db.execute(
            select(NovelReadProgress).where(
                NovelReadProgress.user_id == current_user.id,
                NovelReadProgress.novel_id == novel_id
            )
        )
        progress = progress_result.scalar_one_or_none()
        if progress:
            read_progress = {
                "chapter_id": progress.chapter_id,
                "chapter_num": progress.chapter_num,
                "scroll_position": progress.scroll_position,
                "audio_position": progress.audio_position
            }
    
    # 检查点赞和收藏状态
    is_liked = False
    is_collected = False
    if current_user:
        from app.models.community import NovelLike, NovelCollect
        like_result = await db.execute(
            select(NovelLike).where(
                NovelLike.novel_id == novel_id,
                NovelLike.user_id == current_user.id
            )
        )
        is_liked = like_result.scalar_one_or_none() is not None
        
        collect_result = await db.execute(
            select(NovelCollect).where(
                NovelCollect.novel_id == novel_id,
                NovelCollect.user_id == current_user.id
            )
        )
        is_collected = collect_result.scalar_one_or_none() is not None
    
    # 获取章节列表
    chapters_result = await db.execute(
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_num)
    )
    chapters = chapters_result.scalars().all()
    
    # 获取分类名称
    category_name = None
    if novel.category_id:
        cat_result = await db.execute(
            select(NovelCategory).where(NovelCategory.id == novel.category_id)
        )
        cat = cat_result.scalar_one_or_none()
        if cat:
            category_name = cat.name
    
    return {
        "id": novel.id,
        "title": novel.title,
        "author": novel.author,
        "cover": novel.cover,
        "description": novel.description,
        "novel_type": novel.novel_type,
        "category_name": category_name,
        "view_count": novel.view_count,
        "like_count": novel.like_count,
        "chapter_count": novel.chapter_count,
        "status": novel.status,
        "is_vip": is_vip,
        "is_liked": is_liked,
        "is_collected": is_collected,
        "read_progress": read_progress,
        "chapters": [
            {
                "id": c.id, 
                "num": c.chapter_num, 
                "title": c.title, 
                "is_free": c.is_free,
                "audio_url": c.audio_url if novel.novel_type == "audio" else None
            }
            for c in chapters
        ]
    }


@router.get("/novel/{novel_id}/chapter/{chapter_id}")
async def get_novel_chapter(
    novel_id: int,
    chapter_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
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
    
    # 检查是否需要VIP权限
    if not chapter.is_free:
        is_vip = False
        if current_user:
            from app.models.user import UserVIP
            vip_result = await db.execute(
                select(UserVIP).where(UserVIP.user_id == current_user.id)
            )
            vip = vip_result.scalar_one_or_none()
            if vip and vip.is_active and vip.expire_date and vip.expire_date > datetime.utcnow():
                is_vip = True
        
        if not is_vip:
            raise HTTPException(status_code=403, detail="此章节需要VIP才能阅读")
    
    # 获取上一章和下一章信息
    prev_chapter = None
    next_chapter = None
    
    prev_result = await db.execute(
        select(NovelChapter).where(
            NovelChapter.novel_id == novel_id,
            NovelChapter.chapter_num < chapter.chapter_num
        ).order_by(desc(NovelChapter.chapter_num)).limit(1)
    )
    prev = prev_result.scalar_one_or_none()
    if prev:
        prev_chapter = {"id": prev.id, "title": prev.title}
    
    next_result = await db.execute(
        select(NovelChapter).where(
            NovelChapter.novel_id == novel_id,
            NovelChapter.chapter_num > chapter.chapter_num
        ).order_by(NovelChapter.chapter_num).limit(1)
    )
    nxt = next_result.scalar_one_or_none()
    if nxt:
        next_chapter = {"id": nxt.id, "title": nxt.title, "is_free": nxt.is_free}
    
    return {
        "id": chapter.id,
        "novel_id": chapter.novel_id,
        "chapter_num": chapter.chapter_num,
        "title": chapter.title,
        "content": chapter.content,
        "audio_url": chapter.audio_url,
        "is_free": chapter.is_free,
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter
    }


# ========== 阅读进度API ==========

from pydantic import BaseModel as PydanticBaseModel

class ReadProgressUpdate(PydanticBaseModel):
    chapter_id: int
    chapter_num: int
    scroll_position: float = 0
    audio_position: float = 0

@router.post("/novel/{novel_id}/progress")
async def save_read_progress(
    novel_id: int,
    data: ReadProgressUpdate,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """保存阅读进度"""
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    from app.models.community import NovelReadProgress
    
    # 查找现有进度
    result = await db.execute(
        select(NovelReadProgress).where(
            NovelReadProgress.user_id == current_user.id,
            NovelReadProgress.novel_id == novel_id
        )
    )
    progress = result.scalar_one_or_none()
    
    if progress:
        # 更新进度
        progress.chapter_id = data.chapter_id
        progress.chapter_num = data.chapter_num
        progress.scroll_position = data.scroll_position
        progress.audio_position = data.audio_position
    else:
        # 创建新进度
        progress = NovelReadProgress(
            user_id=current_user.id,
            novel_id=novel_id,
            chapter_id=data.chapter_id,
            chapter_num=data.chapter_num,
            scroll_position=data.scroll_position,
            audio_position=data.audio_position
        )
        db.add(progress)
    
    await db.commit()
    return {"success": True}


@router.get("/novel/{novel_id}/progress")
async def get_read_progress(
    novel_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取阅读进度"""
    if not current_user:
        return {"progress": None}
    
    from app.models.community import NovelReadProgress
    
    result = await db.execute(
        select(NovelReadProgress).where(
            NovelReadProgress.user_id == current_user.id,
            NovelReadProgress.novel_id == novel_id
        )
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        return {"progress": None}
    
    return {
        "progress": {
            "chapter_id": progress.chapter_id,
            "chapter_num": progress.chapter_num,
            "scroll_position": progress.scroll_position,
            "audio_position": progress.audio_position
        }
    }


# ========== 图集评论API ==========

class CommentCreate(BaseModel):
    content: str

@router.get("/gallery/{gallery_id}/comments")
async def get_gallery_comments(
    gallery_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取图集评论"""
    from app.models.community import GalleryComment, GalleryCommentLike
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(GalleryComment)
        .where(GalleryComment.gallery_id == gallery_id)
        .order_by(desc(GalleryComment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    comments = result.scalars().all()
    
    # 获取用户信息
    comment_list = []
    for c in comments:
        user_result = await db.execute(
            select(User).options(selectinload(User.vip)).where(User.id == c.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        # 检查当前用户是否点赞
        is_liked = False
        if current_user:
            try:
                like_result = await db.execute(
                    select(GalleryCommentLike).where(
                        GalleryCommentLike.comment_id == c.id,
                        GalleryCommentLike.user_id == current_user.id
                    )
                )
                is_liked = like_result.scalar_one_or_none() is not None
            except:
                pass
        
        comment_list.append({
            "id": c.id,
            "content": c.content,
            "image_url": c.image_url,
            "user_id": c.user_id,
            "user_nickname": user.nickname if user else "用户",
            "user_avatar": user.avatar if user else None,
            "user_vip_level": user.vip.vip_level if user and user.vip else 0,
            "like_count": c.like_count or 0,
            "reply_count": c.reply_count or 0,
            "is_pinned": c.is_pinned or False,
            "is_official": c.is_official or False,
            "is_liked": is_liked,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    
    return comment_list

@router.post("/gallery/{gallery_id}/comment")
async def create_gallery_comment(
    gallery_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """发表图集评论（支持图片）"""
    from app.models.community import GalleryComment
    import os
    import uuid
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    content = ""
    image_url = None
    
    # 检查 Content-Type
    content_type = request.headers.get("content-type", "")
    print(f"[DEBUG] Content-Type: {content_type}")
    
    if "multipart/form-data" in content_type:
        # FormData 方式
        form = await request.form()
        content = form.get("content", "") or ""
        image = form.get("image")
        print(f"[DEBUG] FormData content: '{content}', image: {image}")
        
        if image and hasattr(image, 'filename') and image.filename:
            ext = os.path.splitext(image.filename)[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            upload_dir = "uploads/comments"
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            
            file_content = await image.read()
            with open(filepath, "wb") as f:
                f.write(file_content)
            
            image_url = f"/uploads/comments/{filename}"
    else:
        # JSON 方式
        try:
            data = await request.json()
            content = data.get("content", "") or ""
            print(f"[DEBUG] JSON content: '{content}'")
        except Exception as e:
            print(f"[DEBUG] JSON parse error: {e}")
    
    print(f"[DEBUG] Final - content: '{content}', image_url: {image_url}")
    
    if not str(content).strip() and not image_url:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    
    # 检查图集是否存在
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    # 创建评论
    comment = GalleryComment(
        gallery_id=gallery_id,
        user_id=current_user.id,
        content=str(content),
        image_url=image_url
    )
    db.add(comment)
    
    # 更新评论数
    gallery.comment_count = (gallery.comment_count or 0) + 1
    
    await db.commit()
    
    return {"success": True, "message": "评论成功"}


# ========== 图集点赞收藏API ==========

@router.post("/gallery/{gallery_id}/like")
async def toggle_gallery_like(
    gallery_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """点赞/取消点赞图集"""
    from app.models.community import GalleryLike
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查图集是否存在
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(GalleryLike).where(
            GalleryLike.gallery_id == gallery_id,
            GalleryLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        gallery.like_count = max(0, (gallery.like_count or 0) - 1)
        liked = False
    else:
        # 点赞
        new_like = GalleryLike(gallery_id=gallery_id, user_id=current_user.id)
        db.add(new_like)
        gallery.like_count = (gallery.like_count or 0) + 1
        liked = True
    
    await db.commit()
    
    return {"liked": liked, "like_count": gallery.like_count}


@router.post("/gallery/{gallery_id}/collect")
async def toggle_gallery_collect(
    gallery_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """收藏/取消收藏图集"""
    from app.models.community import GalleryCollect
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查图集是否存在
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    if not gallery:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    # 检查是否已收藏
    collect_result = await db.execute(
        select(GalleryCollect).where(
            GalleryCollect.gallery_id == gallery_id,
            GalleryCollect.user_id == current_user.id
        )
    )
    existing_collect = collect_result.scalar_one_or_none()
    
    if existing_collect:
        # 取消收藏
        await db.delete(existing_collect)
        gallery.collect_count = max(0, (gallery.collect_count or 0) - 1)
        collected = False
    else:
        # 收藏
        new_collect = GalleryCollect(gallery_id=gallery_id, user_id=current_user.id)
        db.add(new_collect)
        gallery.collect_count = (gallery.collect_count or 0) + 1
        collected = True
    
    await db.commit()
    
    return {"collected": collected, "collect_count": gallery.collect_count}


# ========== 评论点赞API ==========

@router.post("/comment/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """点赞/取消点赞评论"""
    from app.models.community import GalleryComment, GalleryCommentLike
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查评论是否存在
    result = await db.execute(select(GalleryComment).where(GalleryComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(GalleryCommentLike).where(
            GalleryCommentLike.comment_id == comment_id,
            GalleryCommentLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        comment.like_count = max(0, (comment.like_count or 0) - 1)
        liked = False
    else:
        # 点赞
        new_like = GalleryCommentLike(comment_id=comment_id, user_id=current_user.id)
        db.add(new_like)
        comment.like_count = (comment.like_count or 0) + 1
        liked = True
    
    await db.commit()
    
    return {"liked": liked, "like_count": comment.like_count}


# ========== 用户收藏列表API ==========

from app.api.deps import get_current_user

@router.get("/user/collected/galleries")
async def get_user_collected_galleries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户收藏的图集列表"""
    from app.models.community import GalleryCollect
    
    # 构建查询
    query = (
        select(Gallery)
        .join(GalleryCollect, Gallery.id == GalleryCollect.gallery_id)
        .where(GalleryCollect.user_id == current_user.id)
        .where(Gallery.is_active == True)
        .order_by(desc(GalleryCollect.created_at))
    )
    
    # 计算总数
    count_query = (
        select(func.count(Gallery.id))
        .join(GalleryCollect, Gallery.id == GalleryCollect.gallery_id)
        .where(GalleryCollect.user_id == current_user.id)
        .where(Gallery.is_active == True)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    galleries = result.scalars().all()
    
    return {
        "items": [
            {
                "id": g.id,
                "title": g.title,
                "cover": g.cover,
                "thumbnail": g.cover,
                "view_count": g.view_count,
                "image_count": g.image_count,
                "chapter_count": g.chapter_count,
                "status": "连载中" if g.status == "ongoing" else "已完结"
            }
            for g in galleries
        ],
        "total": total,
        "has_more": (page * page_size) < total
    }


@router.get("/user/collected/novels")
async def get_user_collected_novels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户收藏的小说列表"""
    from app.models.community import NovelCollect
    
    # 构建查询
    query = (
        select(Novel)
        .join(NovelCollect, Novel.id == NovelCollect.novel_id)
        .where(NovelCollect.user_id == current_user.id)
        .where(Novel.is_active == True)
        .order_by(desc(NovelCollect.created_at))
    )
    
    # 计算总数
    count_query = (
        select(func.count(Novel.id))
        .join(NovelCollect, Novel.id == NovelCollect.novel_id)
        .where(NovelCollect.user_id == current_user.id)
        .where(Novel.is_active == True)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    novels = result.scalars().all()
    
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "author": n.author,
                "cover": n.cover,
                "thumbnail": n.cover,
                "view_count": n.view_count,
                "chapter_count": n.chapter_count,
                "status": "连载中" if n.status == "ongoing" else "已完结"
            }
            for n in novels
        ],
        "total": total,
        "has_more": (page * page_size) < total
    }


# ========== 用户喜欢列表API ==========

@router.get("/user/liked/galleries")
async def get_user_liked_galleries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户点赞的图集列表"""
    from app.models.community import GalleryLike
    
    # 构建查询
    query = (
        select(Gallery)
        .join(GalleryLike, Gallery.id == GalleryLike.gallery_id)
        .where(GalleryLike.user_id == current_user.id)
        .where(Gallery.is_active == True)
        .order_by(desc(GalleryLike.created_at))
    )
    
    # 计算总数
    count_query = (
        select(func.count(Gallery.id))
        .join(GalleryLike, Gallery.id == GalleryLike.gallery_id)
        .where(GalleryLike.user_id == current_user.id)
        .where(Gallery.is_active == True)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    galleries = result.scalars().all()
    
    return {
        "items": [
            {
                "id": g.id,
                "title": g.title,
                "cover": g.cover,
                "thumbnail": g.cover,
                "view_count": g.view_count,
                "like_count": g.like_count or 0,
                "image_count": g.image_count,
                "chapter_count": g.chapter_count,
                "status": "连载中" if g.status == "ongoing" else "已完结"
            }
            for g in galleries
        ],
        "total": total,
        "has_more": (page * page_size) < total
    }


@router.get("/user/liked/novels")
async def get_user_liked_novels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户点赞的小说列表"""
    from app.models.community import NovelLike
    
    # 构建查询
    query = (
        select(Novel)
        .join(NovelLike, Novel.id == NovelLike.novel_id)
        .where(NovelLike.user_id == current_user.id)
        .where(Novel.is_active == True)
        .order_by(desc(NovelLike.created_at))
    )
    
    # 计算总数
    count_query = (
        select(func.count(Novel.id))
        .join(NovelLike, Novel.id == NovelLike.novel_id)
        .where(NovelLike.user_id == current_user.id)
        .where(Novel.is_active == True)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    novels = result.scalars().all()
    
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "author": n.author,
                "cover": n.cover,
                "thumbnail": n.cover,
                "view_count": n.view_count,
                "like_count": n.like_count or 0,
                "chapter_count": n.chapter_count,
                "status": "连载中" if n.status == "ongoing" else "已完结"
            }
            for n in novels
        ],
        "total": total,
        "has_more": (page * page_size) < total
    }


# ========== 小说点赞收藏API ==========

@router.post("/novel/{novel_id}/like")
async def toggle_novel_like(
    novel_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """点赞/取消点赞小说"""
    from app.models.community import NovelLike
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查小说是否存在
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(NovelLike).where(
            NovelLike.novel_id == novel_id,
            NovelLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        await db.delete(existing_like)
        novel.like_count = max(0, (novel.like_count or 0) - 1)
        liked = False
    else:
        new_like = NovelLike(novel_id=novel_id, user_id=current_user.id)
        db.add(new_like)
        novel.like_count = (novel.like_count or 0) + 1
        liked = True
    
    await db.commit()
    return {"liked": liked, "like_count": novel.like_count}


@router.post("/novel/{novel_id}/collect")
async def toggle_novel_collect(
    novel_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """收藏/取消收藏小说"""
    from app.models.community import NovelCollect
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查小说是否存在
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 检查是否已收藏
    collect_result = await db.execute(
        select(NovelCollect).where(
            NovelCollect.novel_id == novel_id,
            NovelCollect.user_id == current_user.id
        )
    )
    existing_collect = collect_result.scalar_one_or_none()
    
    if existing_collect:
        await db.delete(existing_collect)
        novel.collect_count = max(0, (novel.collect_count or 0) - 1)
        collected = False
    else:
        new_collect = NovelCollect(novel_id=novel_id, user_id=current_user.id)
        db.add(new_collect)
        novel.collect_count = (novel.collect_count or 0) + 1
        collected = True
    
    await db.commit()
    return {"collected": collected, "collect_count": novel.collect_count}


# ========== 小说评论API ==========

@router.get("/novel/{novel_id}/comments")
async def get_novel_comments(
    novel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """获取小说评论"""
    from app.models.community import NovelComment, NovelCommentLike
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(NovelComment)
        .where(NovelComment.novel_id == novel_id)
        .order_by(desc(NovelComment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    comments = result.scalars().all()
    
    # 获取用户信息
    comment_list = []
    for c in comments:
        user_result = await db.execute(
            select(User).options(selectinload(User.vip)).where(User.id == c.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        # 检查当前用户是否点赞
        is_liked = False
        if current_user:
            try:
                like_result = await db.execute(
                    select(NovelCommentLike).where(
                        NovelCommentLike.comment_id == c.id,
                        NovelCommentLike.user_id == current_user.id
                    )
                )
                is_liked = like_result.scalar_one_or_none() is not None
            except:
                pass
        
        comment_list.append({
            "id": c.id,
            "content": c.content,
            "image_url": c.image_url,
            "user_id": c.user_id,
            "user_nickname": user.nickname if user else "用户",
            "user_avatar": user.avatar if user else None,
            "user_vip_level": user.vip.vip_level if user and user.vip else 0,
            "like_count": c.like_count or 0,
            "reply_count": c.reply_count or 0,
            "is_pinned": c.is_pinned or False,
            "is_official": c.is_official or False,
            "is_liked": is_liked,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    
    return comment_list


@router.post("/novel/{novel_id}/comment")
async def create_novel_comment(
    novel_id: int,
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """发表小说评论（支持图片）"""
    from app.models.community import NovelComment
    import os
    import uuid
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    content = ""
    image_url = None
    
    # 检查 Content-Type
    content_type = request.headers.get("content-type", "")
    
    if "multipart/form-data" in content_type:
        # FormData 方式
        form = await request.form()
        content = form.get("content", "") or ""
        image = form.get("image")
        
        if image and hasattr(image, 'filename') and image.filename:
            ext = os.path.splitext(image.filename)[1] or '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            upload_dir = "uploads/comments"
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            
            file_content = await image.read()
            with open(filepath, "wb") as f:
                f.write(file_content)
            
            image_url = f"/uploads/comments/{filename}"
    else:
        # JSON 方式
        try:
            data = await request.json()
            content = data.get("content", "") or ""
        except Exception as e:
            pass
    
    if not str(content).strip() and not image_url:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    
    # 检查小说是否存在
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 创建评论
    comment = NovelComment(
        novel_id=novel_id,
        user_id=current_user.id,
        content=str(content),
        image_url=image_url
    )
    db.add(comment)
    
    # 更新评论数
    novel.comment_count = (novel.comment_count or 0) + 1
    
    await db.commit()
    
    return {"success": True, "message": "评论成功"}


@router.post("/novel-comment/{comment_id}/like")
async def toggle_novel_comment_like(
    comment_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """点赞/取消点赞小说评论"""
    from app.models.community import NovelComment, NovelCommentLike
    
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    
    # 检查评论是否存在
    result = await db.execute(select(NovelComment).where(NovelComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查是否已点赞
    like_result = await db.execute(
        select(NovelCommentLike).where(
            NovelCommentLike.comment_id == comment_id,
            NovelCommentLike.user_id == current_user.id
        )
    )
    existing_like = like_result.scalar_one_or_none()
    
    if existing_like:
        # 取消点赞
        await db.delete(existing_like)
        comment.like_count = max(0, (comment.like_count or 0) - 1)
        liked = False
    else:
        # 点赞
        new_like = NovelCommentLike(comment_id=comment_id, user_id=current_user.id)
        db.add(new_like)
        comment.like_count = (comment.like_count or 0) + 1
        liked = True
    
    await db.commit()
    
    return {"liked": liked, "like_count": comment.like_count}
