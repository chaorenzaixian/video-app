"""
图集小说后台管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.community import (
    GalleryCategory, Gallery, 
    NovelCategory, Novel, NovelChapter
)
from app.services.image_service import ImageService

router = APIRouter(prefix="/admin/gallery-novel", tags=["图集小说管理"])


# ========== 文件上传 ==========

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    subdir: str = Form("gallery"),
    admin: User = Depends(get_current_admin)
):
    """上传图片（图集封面、图集图片、小说封面等）"""
    if file.content_type not in ImageService.SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    content = await file.read()
    valid, error = ImageService.validate_image(content, file.content_type)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    try:
        result = await ImageService.save_image(
            content=content,
            subdir=subdir,
            convert_webp=True
        )
        return {"url": result["url"], "filename": result["filename"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/upload/images")
async def upload_multiple_images(
    files: List[UploadFile] = File(...),
    subdir: str = Form("gallery"),
    admin: User = Depends(get_current_admin)
):
    """批量上传图片"""
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="单次最多上传50张图片")
    
    results = []
    errors = []
    
    for i, file in enumerate(files):
        if file.content_type not in ImageService.SUPPORTED_FORMATS:
            errors.append({"index": i, "name": file.filename, "error": "不支持的格式"})
            continue
        
        try:
            content = await file.read()
            valid, error = ImageService.validate_image(content, file.content_type)
            if not valid:
                errors.append({"index": i, "name": file.filename, "error": error})
                continue
            
            result = await ImageService.save_image(
                content=content,
                subdir=subdir,
                convert_webp=True
            )
            results.append({"url": result["url"], "filename": result["filename"]})
        except Exception as e:
            errors.append({"index": i, "name": file.filename, "error": str(e)})
    
    return {"urls": results, "errors": errors, "success_count": len(results), "error_count": len(errors)}


@router.post("/upload/audio")
async def upload_audio(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    """上传音频文件（有声小说章节）"""
    allowed_types = {'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/aac'}
    
    # 有些浏览器可能不发送正确的 content_type
    if file.content_type not in allowed_types and not file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
        raise HTTPException(status_code=400, detail="不支持的音频格式，支持 mp3/wav/ogg/m4a/aac")
    
    content = await file.read()
    
    # 限制 100MB
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="音频文件不能超过100MB")
    
    import os
    import uuid
    from app.core.config import settings
    
    # 保存文件
    filename = f"{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
    save_dir = os.path.join(settings.UPLOAD_DIR, "audio")
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(content)
    
    return {"url": f"/uploads/audio/{filename}", "filename": filename}


@router.post("/upload/video")
async def upload_video(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin)
):
    """上传视频文件（帖子短视频）"""
    allowed_types = {'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'}
    allowed_exts = ('.mp4', '.webm', '.mov', '.avi', '.mkv')
    
    if file.content_type not in allowed_types and not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="不支持的视频格式，支持 mp4/webm/mov/avi/mkv")
    
    content = await file.read()
    
    # 限制 500MB
    if len(content) > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="视频文件不能超过500MB")
    
    import os
    import uuid
    from app.core.config import settings
    
    # 保存文件
    ext = os.path.splitext(file.filename)[1].lower() or '.mp4'
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(settings.UPLOAD_DIR, "video")
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(content)
    
    return {"url": f"/uploads/video/{filename}", "filename": filename, "size": len(content)}


# ========== Schemas ==========

class GalleryCategoryCreate(BaseModel):
    name: str
    sort_order: int = 0

class GalleryCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class GalleryCreate(BaseModel):
    category_id: Optional[int] = None
    title: str
    cover: str
    images: List[str] = []
    description: Optional[str] = None
    chapter_count: int = 1
    status: str = "ongoing"
    is_hot: bool = False
    is_recommended: bool = False
    sort_order: int = 0

class GalleryUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    cover: Optional[str] = None
    images: Optional[List[str]] = None
    description: Optional[str] = None
    chapter_count: Optional[int] = None
    status: Optional[str] = None
    is_hot: Optional[bool] = None
    is_recommended: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class NovelCategoryCreate(BaseModel):
    name: str
    novel_type: str = "text"
    sort_order: int = 0

class NovelCategoryUpdate(BaseModel):
    name: Optional[str] = None
    novel_type: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class NovelCreate(BaseModel):
    category_id: Optional[int] = None
    title: str
    author: Optional[str] = None
    cover: str
    description: Optional[str] = None
    novel_type: str = "text"
    status: str = "ongoing"
    is_hot: bool = False
    is_recommended: bool = False
    sort_order: int = 0

class NovelUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    cover: Optional[str] = None
    description: Optional[str] = None
    novel_type: Optional[str] = None
    status: Optional[str] = None
    is_hot: Optional[bool] = None
    is_recommended: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class ChapterCreate(BaseModel):
    chapter_num: int
    title: str
    content: Optional[str] = None
    audio_url: Optional[str] = None
    is_free: bool = True

class ChapterUpdate(BaseModel):
    chapter_num: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    audio_url: Optional[str] = None
    is_free: Optional[bool] = None


# ========== 图集分类管理 ==========

@router.get("/gallery/categories")
async def get_gallery_categories(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取图集分类列表"""
    result = await db.execute(
        select(GalleryCategory).order_by(desc(GalleryCategory.sort_order), GalleryCategory.id)
    )
    categories = result.scalars().all()
    
    items = []
    for c in categories:
        # 统计该分类下的图集数量
        count_result = await db.execute(
            select(func.count(Gallery.id)).where(
                Gallery.category_id == c.id,
                Gallery.is_active == True
            )
        )
        gallery_count = count_result.scalar() or 0
        
        items.append({
            "id": c.id,
            "name": c.name,
            "sort_order": c.sort_order,
            "is_active": c.is_active,
            "gallery_count": gallery_count,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    
    return items


@router.post("/gallery/categories")
async def create_gallery_category(
    data: GalleryCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建图集分类"""
    category = GalleryCategory(
        name=data.name,
        sort_order=data.sort_order
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return {"id": category.id, "message": "创建成功"}


@router.put("/gallery/categories/{category_id}")
async def update_gallery_category(
    category_id: int,
    data: GalleryCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新图集分类"""
    result = await db.execute(select(GalleryCategory).where(GalleryCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if data.name is not None:
        category.name = data.name
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    if data.is_active is not None:
        category.is_active = data.is_active
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/gallery/categories/{category_id}")
async def delete_gallery_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除图集分类"""
    result = await db.execute(select(GalleryCategory).where(GalleryCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category.is_active = False
    await db.commit()
    return {"message": "删除成功"}


# ========== 图集管理 ==========

@router.get("/galleries")
async def get_galleries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    is_hot: Optional[bool] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取图集列表"""
    query = select(Gallery).where(Gallery.is_active == True)
    count_query = select(func.count(Gallery.id)).where(Gallery.is_active == True)
    
    if category_id:
        query = query.where(Gallery.category_id == category_id)
        count_query = count_query.where(Gallery.category_id == category_id)
    
    if keyword:
        query = query.where(Gallery.title.contains(keyword))
        count_query = count_query.where(Gallery.title.contains(keyword))
    
    if status:
        query = query.where(Gallery.status == status)
        count_query = count_query.where(Gallery.status == status)
    
    if is_hot is not None:
        query = query.where(Gallery.is_hot == is_hot)
        count_query = count_query.where(Gallery.is_hot == is_hot)
    
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(Gallery.sort_order), desc(Gallery.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    galleries = result.scalars().all()
    
    items = []
    for g in galleries:
        # 获取分类名称
        category_name = None
        if g.category_id:
            cat_result = await db.execute(
                select(GalleryCategory).where(GalleryCategory.id == g.category_id)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                category_name = cat.name
        
        items.append({
            "id": g.id,
            "category_id": g.category_id,
            "category_name": category_name,
            "title": g.title,
            "cover": g.cover,
            "images": g.images or [],
            "description": g.description,
            "view_count": g.view_count,
            "like_count": g.like_count,
            "image_count": g.image_count,
            "chapter_count": g.chapter_count,
            "status": g.status,
            "is_hot": g.is_hot,
            "is_recommended": g.is_recommended,
            "sort_order": g.sort_order,
            "created_at": g.created_at.isoformat() if g.created_at else None
        })
    
    return {
        "items": items,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.post("/galleries")
async def create_gallery(
    data: GalleryCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建图集"""
    gallery = Gallery(
        category_id=data.category_id,
        title=data.title,
        cover=data.cover,
        images=data.images,
        description=data.description,
        image_count=len(data.images),
        chapter_count=data.chapter_count,
        status=data.status,
        is_hot=data.is_hot,
        is_recommended=data.is_recommended,
        sort_order=data.sort_order
    )
    db.add(gallery)
    await db.commit()
    await db.refresh(gallery)
    
    return {"id": gallery.id, "message": "创建成功"}


@router.put("/galleries/{gallery_id}")
async def update_gallery(
    gallery_id: int,
    data: GalleryUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新图集"""
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    
    if not gallery:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    if data.category_id is not None:
        gallery.category_id = data.category_id
    if data.title is not None:
        gallery.title = data.title
    if data.cover is not None:
        gallery.cover = data.cover
    if data.images is not None:
        gallery.images = data.images
        gallery.image_count = len(data.images)
    if data.description is not None:
        gallery.description = data.description
    if data.chapter_count is not None:
        gallery.chapter_count = data.chapter_count
    if data.status is not None:
        gallery.status = data.status
    if data.is_hot is not None:
        gallery.is_hot = data.is_hot
    if data.is_recommended is not None:
        gallery.is_recommended = data.is_recommended
    if data.is_active is not None:
        gallery.is_active = data.is_active
    if data.sort_order is not None:
        gallery.sort_order = data.sort_order
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/galleries/{gallery_id}")
async def delete_gallery(
    gallery_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除图集"""
    result = await db.execute(select(Gallery).where(Gallery.id == gallery_id))
    gallery = result.scalar_one_or_none()
    
    if not gallery:
        raise HTTPException(status_code=404, detail="图集不存在")
    
    gallery.is_active = False
    await db.commit()
    return {"message": "删除成功"}


# ========== 小说分类管理 ==========

@router.get("/novel/categories")
async def get_novel_categories(
    novel_type: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取小说分类列表"""
    query = select(NovelCategory).order_by(desc(NovelCategory.sort_order), NovelCategory.id)
    
    if novel_type:
        query = query.where(NovelCategory.novel_type == novel_type)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    items = []
    for c in categories:
        # 统计该分类下的小说数量
        count_result = await db.execute(
            select(func.count(Novel.id)).where(
                Novel.category_id == c.id,
                Novel.is_active == True
            )
        )
        novel_count = count_result.scalar() or 0
        
        items.append({
            "id": c.id,
            "name": c.name,
            "novel_type": c.novel_type,
            "sort_order": c.sort_order,
            "is_active": c.is_active,
            "novel_count": novel_count,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    
    return items


@router.post("/novel/categories")
async def create_novel_category(
    data: NovelCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建小说分类"""
    category = NovelCategory(
        name=data.name,
        novel_type=data.novel_type,
        sort_order=data.sort_order
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return {"id": category.id, "message": "创建成功"}


@router.put("/novel/categories/{category_id}")
async def update_novel_category(
    category_id: int,
    data: NovelCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新小说分类"""
    result = await db.execute(select(NovelCategory).where(NovelCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if data.name is not None:
        category.name = data.name
    if data.novel_type is not None:
        category.novel_type = data.novel_type
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    if data.is_active is not None:
        category.is_active = data.is_active
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/novel/categories/{category_id}")
async def delete_novel_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除小说分类"""
    result = await db.execute(select(NovelCategory).where(NovelCategory.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category.is_active = False
    await db.commit()
    return {"message": "删除成功"}


# ========== 小说管理 ==========

@router.get("/novels")
async def get_novels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    novel_type: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    is_hot: Optional[bool] = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取小说列表"""
    query = select(Novel).where(Novel.is_active == True)
    count_query = select(func.count(Novel.id)).where(Novel.is_active == True)
    
    if category_id:
        query = query.where(Novel.category_id == category_id)
        count_query = count_query.where(Novel.category_id == category_id)
    
    if novel_type:
        query = query.where(Novel.novel_type == novel_type)
        count_query = count_query.where(Novel.novel_type == novel_type)
    
    if keyword:
        query = query.where(Novel.title.contains(keyword))
        count_query = count_query.where(Novel.title.contains(keyword))
    
    if status:
        query = query.where(Novel.status == status)
        count_query = count_query.where(Novel.status == status)
    
    if is_hot is not None:
        query = query.where(Novel.is_hot == is_hot)
        count_query = count_query.where(Novel.is_hot == is_hot)
    
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(Novel.sort_order), desc(Novel.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    novels = result.scalars().all()
    
    items = []
    for n in novels:
        # 获取分类名称
        category_name = None
        if n.category_id:
            cat_result = await db.execute(
                select(NovelCategory).where(NovelCategory.id == n.category_id)
            )
            cat = cat_result.scalar_one_or_none()
            if cat:
                category_name = cat.name
        
        items.append({
            "id": n.id,
            "category_id": n.category_id,
            "category_name": category_name,
            "title": n.title,
            "author": n.author,
            "cover": n.cover,
            "description": n.description,
            "novel_type": n.novel_type,
            "view_count": n.view_count,
            "like_count": n.like_count,
            "chapter_count": n.chapter_count,
            "status": n.status,
            "is_hot": n.is_hot,
            "is_recommended": n.is_recommended,
            "sort_order": n.sort_order,
            "created_at": n.created_at.isoformat() if n.created_at else None
        })
    
    return {
        "items": items,
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }


@router.post("/novels")
async def create_novel(
    data: NovelCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建小说"""
    novel = Novel(
        category_id=data.category_id,
        title=data.title,
        author=data.author,
        cover=data.cover,
        description=data.description,
        novel_type=data.novel_type,
        status=data.status,
        is_hot=data.is_hot,
        is_recommended=data.is_recommended,
        sort_order=data.sort_order
    )
    db.add(novel)
    await db.commit()
    await db.refresh(novel)
    
    return {"id": novel.id, "message": "创建成功"}


@router.put("/novels/{novel_id}")
async def update_novel(
    novel_id: int,
    data: NovelUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新小说"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    if data.category_id is not None:
        novel.category_id = data.category_id
    if data.title is not None:
        novel.title = data.title
    if data.author is not None:
        novel.author = data.author
    if data.cover is not None:
        novel.cover = data.cover
    if data.description is not None:
        novel.description = data.description
    if data.novel_type is not None:
        novel.novel_type = data.novel_type
    if data.status is not None:
        novel.status = data.status
    if data.is_hot is not None:
        novel.is_hot = data.is_hot
    if data.is_recommended is not None:
        novel.is_recommended = data.is_recommended
    if data.is_active is not None:
        novel.is_active = data.is_active
    if data.sort_order is not None:
        novel.sort_order = data.sort_order
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/novels/{novel_id}")
async def delete_novel(
    novel_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除小说"""
    result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = result.scalar_one_or_none()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    novel.is_active = False
    await db.commit()
    return {"message": "删除成功"}


# ========== 小说章节管理 ==========

@router.get("/novels/{novel_id}/chapters")
async def get_novel_chapters(
    novel_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取小说章节列表"""
    result = await db.execute(
        select(NovelChapter)
        .where(NovelChapter.novel_id == novel_id)
        .order_by(NovelChapter.chapter_num)
    )
    chapters = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "novel_id": c.novel_id,
            "chapter_num": c.chapter_num,
            "title": c.title,
            "content_length": len(c.content) if c.content else 0,
            "audio_url": c.audio_url,
            "is_free": c.is_free,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in chapters
    ]


@router.post("/novels/{novel_id}/chapters")
async def create_chapter(
    novel_id: int,
    data: ChapterCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建章节"""
    # 检查小说是否存在
    novel_result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = novel_result.scalar_one_or_none()
    
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    chapter = NovelChapter(
        novel_id=novel_id,
        chapter_num=data.chapter_num,
        title=data.title,
        content=data.content,
        audio_url=data.audio_url,
        is_free=data.is_free
    )
    db.add(chapter)
    
    # 更新小说章节数
    novel.chapter_count = (novel.chapter_count or 0) + 1
    
    await db.commit()
    await db.refresh(chapter)
    
    return {"id": chapter.id, "message": "创建成功"}


@router.put("/novels/{novel_id}/chapters/{chapter_id}")
async def update_chapter(
    novel_id: int,
    chapter_id: int,
    data: ChapterUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新章节"""
    result = await db.execute(
        select(NovelChapter).where(
            NovelChapter.id == chapter_id,
            NovelChapter.novel_id == novel_id
        )
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    if data.chapter_num is not None:
        chapter.chapter_num = data.chapter_num
    if data.title is not None:
        chapter.title = data.title
    if data.content is not None:
        chapter.content = data.content
    if data.audio_url is not None:
        chapter.audio_url = data.audio_url
    if data.is_free is not None:
        chapter.is_free = data.is_free
    
    await db.commit()
    return {"message": "更新成功"}


@router.delete("/novels/{novel_id}/chapters/{chapter_id}")
async def delete_chapter(
    novel_id: int,
    chapter_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除章节"""
    result = await db.execute(
        select(NovelChapter).where(
            NovelChapter.id == chapter_id,
            NovelChapter.novel_id == novel_id
        )
    )
    chapter = result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 更新小说章节数
    novel_result = await db.execute(select(Novel).where(Novel.id == novel_id))
    novel = novel_result.scalar_one_or_none()
    if novel:
        novel.chapter_count = max(0, (novel.chapter_count or 0) - 1)
    
    await db.delete(chapter)
    await db.commit()
    
    return {"message": "删除成功"}
