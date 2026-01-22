"""
暗网视频后台管理API
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, text
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.darkweb import DarkwebCategory, DarkwebTag, DarkwebVideo, DarkwebView
from app.models.video import VideoStatus
from app.models.system_config import SystemConfig
from app.services.video_processor import VideoProcessor

router = APIRouter(prefix="/admin/darkweb", tags=["暗网视频管理"])


# ========== Schemas ==========
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    parent_id: Optional[int] = None
    level: int = 1
    video_count: int = 0
    children: List["CategoryResponse"] = []
    
    class Config:
        from_attributes = True

CategoryResponse.model_rebuild()


class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: int
    name: str
    use_count: int = 0
    
    class Config:
        from_attributes = True


class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    original_url: Optional[str] = None
    hls_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: float = 0
    category_id: Optional[int] = None
    tags: List[str] = []
    is_featured: bool = False


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    hls_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: Optional[float] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None


class VideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    hls_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: float = 0
    status: str
    view_count: int = 0
    like_count: int = 0
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tags: List[str] = []
    is_featured: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    page: int
    page_size: int


class ConfigUpdate(BaseModel):
    min_vip_level: int


# ========== 分类管理 ==========
@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取所有分类（带层级和视频数量）"""
    result = await db.execute(
        select(DarkwebCategory).order_by(DarkwebCategory.level, DarkwebCategory.sort_order)
    )
    all_categories = result.scalars().all()
    
    count_result = await db.execute(
        select(DarkwebVideo.category_id, func.count(DarkwebVideo.id))
        .group_by(DarkwebVideo.category_id)
    )
    count_map = {r[0]: r[1] for r in count_result.fetchall()}
    
    parent_categories = [c for c in all_categories if c.level == 1]
    child_categories = [c for c in all_categories if c.level == 2]
    
    children_map = {}
    for child in child_categories:
        if child.parent_id not in children_map:
            children_map[child.parent_id] = []
        child_resp = CategoryResponse(
            id=child.id,
            name=child.name,
            description=child.description,
            icon=child.icon,
            sort_order=child.sort_order or 0,
            is_active=child.is_active if child.is_active is not None else True,
            parent_id=child.parent_id,
            level=child.level or 2,
            video_count=count_map.get(child.id, 0),
            children=[]
        )
        children_map[child.parent_id].append(child_resp)
    
    categories = []
    for parent in parent_categories:
        children = children_map.get(parent.id, [])
        total_count = count_map.get(parent.id, 0) + sum(c.video_count for c in children)
        cat = CategoryResponse(
            id=parent.id,
            name=parent.name,
            description=parent.description,
            icon=parent.icon,
            sort_order=parent.sort_order or 0,
            is_active=parent.is_active if parent.is_active is not None else True,
            parent_id=parent.parent_id,
            level=parent.level or 1,
            video_count=total_count,
            children=children
        )
        categories.append(cat)
    
    return categories


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建分类"""
    level = 1
    if data.parent_id:
        parent_result = await db.execute(
            select(DarkwebCategory).where(DarkwebCategory.id == data.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="父分类不存在")
        if parent.level != 1:
            raise HTTPException(status_code=400, detail="只能在一级分类下创建二级分类")
        level = 2
    
    category = DarkwebCategory(
        name=data.name,
        description=data.description,
        icon=data.icon,
        sort_order=data.sort_order,
        parent_id=data.parent_id,
        level=level,
        is_active=True
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_id=category.parent_id,
        level=category.level,
        video_count=0,
        children=[]
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新分类"""
    result = await db.execute(
        select(DarkwebCategory).where(DarkwebCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if data.name is not None:
        category.name = data.name
    if data.description is not None:
        category.description = data.description
    if data.icon is not None:
        category.icon = data.icon
    if data.sort_order is not None:
        category.sort_order = data.sort_order
    if data.is_active is not None:
        category.is_active = data.is_active
    
    await db.commit()
    await db.refresh(category)
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_id=category.parent_id,
        level=category.level,
        video_count=0,
        children=[]
    )


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除分类"""
    result = await db.execute(
        select(DarkwebCategory).where(DarkwebCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    if category.level == 1:
        child_result = await db.execute(
            select(func.count(DarkwebCategory.id)).where(DarkwebCategory.parent_id == category_id)
        )
        child_count = child_result.scalar()
        if child_count > 0:
            raise HTTPException(status_code=400, detail="请先删除子分类")
    
    video_result = await db.execute(
        select(func.count(DarkwebVideo.id)).where(DarkwebVideo.category_id == category_id)
    )
    video_count = video_result.scalar()
    if video_count > 0:
        raise HTTPException(status_code=400, detail="该分类下有视频，无法删除")
    
    await db.delete(category)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 标签管理 ==========
@router.get("/tags", response_model=List[TagResponse])
async def get_tags(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取所有标签"""
    result = await db.execute(
        select(DarkwebTag)
        .order_by(DarkwebTag.use_count.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()


@router.post("/tags", response_model=TagResponse)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建标签"""
    result = await db.execute(
        select(DarkwebTag).where(DarkwebTag.name == data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="标签已存在")
    
    tag = DarkwebTag(name=data.name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    return tag


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除标签"""
    result = await db.execute(
        select(DarkwebTag).where(DarkwebTag.id == tag_id)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    await db.delete(tag)
    await db.commit()
    
    return {"message": "删除成功"}


# ========== 视频管理 ==========
@router.get("/videos", response_model=VideoListResponse)
async def get_videos(
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取视频列表"""
    query = select(DarkwebVideo)
    count_query = select(func.count(DarkwebVideo.id))
    
    if category_id:
        query = query.where(DarkwebVideo.category_id == category_id)
        count_query = count_query.where(DarkwebVideo.category_id == category_id)
    
    if status:
        query = query.where(DarkwebVideo.status == status)
        count_query = count_query.where(DarkwebVideo.status == status)
    
    if keyword:
        query = query.where(DarkwebVideo.title.ilike(f"%{keyword}%"))
        count_query = count_query.where(DarkwebVideo.title.ilike(f"%{keyword}%"))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(DarkwebVideo.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(selectinload(DarkwebVideo.category), selectinload(DarkwebVideo.tags))
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    items = [VideoResponse(
        id=v.id,
        title=v.title,
        description=v.description,
        cover_url=v.cover_url,
        hls_url=v.hls_url,
        preview_url=v.preview_url,
        duration=v.duration,
        status=v.status.value if v.status else "UPLOADING",
        view_count=v.view_count,
        like_count=v.like_count,
        category_id=v.category_id,
        category_name=v.category.name if v.category else None,
        tags=[t.name for t in v.tags],
        is_featured=v.is_featured,
        created_at=v.created_at
    ) for v in videos]
    
    return VideoListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/videos", response_model=VideoResponse)
async def create_video(
    data: VideoCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """创建视频"""
    video = DarkwebVideo(
        title=data.title,
        description=data.description,
        cover_url=data.cover_url,
        original_url=data.original_url,
        hls_url=data.hls_url,
        preview_url=data.preview_url,
        duration=data.duration,
        category_id=data.category_id,
        is_featured=data.is_featured,
        uploader_id=admin.id,
        status=VideoStatus.PUBLISHED if data.hls_url else VideoStatus.UPLOADING
    )
    
    if data.tags:
        for tag_name in data.tags:
            result = await db.execute(
                select(DarkwebTag).where(DarkwebTag.name == tag_name)
            )
            tag = result.scalar_one_or_none()
            if not tag:
                tag = DarkwebTag(name=tag_name)
                db.add(tag)
            tag.use_count += 1
            video.tags.append(tag)
    
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        cover_url=video.cover_url,
        hls_url=video.hls_url,
        preview_url=video.preview_url,
        duration=video.duration,
        status=video.status.value,
        view_count=video.view_count,
        like_count=video.like_count,
        category_id=video.category_id,
        category_name=None,
        tags=data.tags,
        is_featured=video.is_featured,
        created_at=video.created_at
    )


@router.put("/videos/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    data: VideoUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新视频"""
    result = await db.execute(
        select(DarkwebVideo)
        .options(selectinload(DarkwebVideo.category), selectinload(DarkwebVideo.tags))
        .where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if data.title is not None:
        video.title = data.title
    if data.description is not None:
        video.description = data.description
    if data.cover_url is not None:
        video.cover_url = data.cover_url
    if data.hls_url is not None:
        video.hls_url = data.hls_url
    if data.preview_url is not None:
        video.preview_url = data.preview_url
    if data.duration is not None:
        video.duration = data.duration
    if data.category_id is not None:
        video.category_id = data.category_id
    if data.is_featured is not None:
        video.is_featured = data.is_featured
    if data.status is not None:
        video.status = VideoStatus(data.status)
    
    if data.tags is not None:
        video.tags.clear()
        for tag_name in data.tags:
            result = await db.execute(
                select(DarkwebTag).where(DarkwebTag.name == tag_name)
            )
            tag = result.scalar_one_or_none()
            if not tag:
                tag = DarkwebTag(name=tag_name)
                db.add(tag)
            tag.use_count += 1
            video.tags.append(tag)
    
    await db.commit()
    await db.refresh(video)
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        cover_url=video.cover_url,
        hls_url=video.hls_url,
        preview_url=video.preview_url,
        duration=video.duration,
        status=video.status.value,
        view_count=video.view_count,
        like_count=video.like_count,
        category_id=video.category_id,
        category_name=video.category.name if video.category else None,
        tags=[t.name for t in video.tags],
        is_featured=video.is_featured,
        created_at=video.created_at
    )


@router.delete("/videos/{video_id}")
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """删除视频（包括数据库记录和服务器文件）"""
    result = await db.execute(
        select(DarkwebVideo).where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 保存文件路径用于删除
    hls_url = video.hls_url
    cover_url = video.cover_url
    preview_url = video.preview_url
    original_url = video.original_url
    
    # 删除关联数据
    await db.execute(delete(DarkwebView).where(DarkwebView.video_id == video_id))
    
    await db.delete(video)
    await db.commit()
    
    # 删除服务器上的文件
    deleted_files = []
    try:
        # HLS目录
        if hls_url and "/darkweb_hls/" in hls_url:
            hls_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_hls", str(video_id))
            if os.path.exists(hls_dir):
                shutil.rmtree(hls_dir, ignore_errors=True)
                deleted_files.append(f"darkweb_hls/{video_id}/")
        
        # 封面
        if cover_url and "/darkweb_thumbnails/" in cover_url:
            cover_file = os.path.join(settings.UPLOAD_DIR, "darkweb_thumbnails", os.path.basename(cover_url))
            if os.path.exists(cover_file):
                os.remove(cover_file)
                deleted_files.append(f"darkweb_thumbnails/{os.path.basename(cover_url)}")
        
        # 预览视频
        if preview_url and "/darkweb_previews/" in preview_url:
            preview_file = os.path.join(settings.UPLOAD_DIR, "darkweb_previews", os.path.basename(preview_url))
            if os.path.exists(preview_file):
                os.remove(preview_file)
                deleted_files.append(f"darkweb_previews/{os.path.basename(preview_url)}")
        
        # 原始视频文件
        if original_url and "/darkweb_videos/" in original_url:
            original_file = os.path.join(settings.UPLOAD_DIR, "darkweb_videos", os.path.basename(original_url))
            if os.path.exists(original_file):
                os.remove(original_file)
                deleted_files.append(f"darkweb_videos/{os.path.basename(original_url)}")
        elif original_url and os.path.exists(original_url):
            # 如果是绝对路径
            os.remove(original_url)
            deleted_files.append(original_url)
    except Exception as e:
        print(f"删除暗网视频文件时出错: {e}")
    
    return {"message": "删除成功", "deleted_files": deleted_files}


# ========== 配置管理 ==========
@router.get("/config")
async def get_config(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取暗网专区配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "darkweb_min_vip_level")
    )
    config = result.scalar_one_or_none()
    
    return {
        "min_vip_level": int(config.value) if config else 5
    }


@router.put("/config")
async def update_config(
    data: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """更新暗网专区配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "darkweb_min_vip_level")
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = str(data.min_vip_level)
    else:
        config = SystemConfig(
            key="darkweb_min_vip_level",
            value=str(data.min_vip_level),
            description="暗网专区最低VIP等级要求"
        )
        db.add(config)
    
    await db.commit()
    
    return {"message": "配置更新成功", "min_vip_level": data.min_vip_level}


# ========== 统计 ==========
@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """获取暗网专区统计"""
    video_count = await db.execute(select(func.count(DarkwebVideo.id)))
    category_count = await db.execute(select(func.count(DarkwebCategory.id)))
    tag_count = await db.execute(select(func.count(DarkwebTag.id)))
    total_views = await db.execute(select(func.sum(DarkwebVideo.view_count)))
    
    return {
        "video_count": video_count.scalar() or 0,
        "category_count": category_count.scalar() or 0,
        "tag_count": tag_count.scalar() or 0,
        "total_views": total_views.scalar() or 0
    }


# ========== 视频上传 ==========
@router.post("/videos/upload", response_model=VideoResponse)
async def upload_darkweb_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    is_featured: bool = Form(False),
    custom_cover_url: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """上传暗网视频（支持自定义封面）"""
    # 检查文件类型
    allowed_types = ["video/mp4", "video/webm", "video/avi", "video/mov", "video/mkv", 
                     "video/x-msvideo", "video/quicktime", "video/x-matroska"]
    content_type = file.content_type or ""
    if not content_type.startswith("video/") and content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的视频格式"
        )
    
    # 确保目录存在
    darkweb_video_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_videos")
    os.makedirs(darkweb_video_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] or ".mp4"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(darkweb_video_dir, unique_filename)
    
    # 保存视频文件
    content = await file.read()
    max_size = getattr(settings, 'MAX_VIDEO_SIZE', 5 * 1024 * 1024 * 1024)  # 默认5GB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频文件过大"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建视频记录
    video = DarkwebVideo(
        title=title,
        description=description,
        original_url=file_path,
        category_id=category_id if category_id else None,
        uploader_id=admin.id,
        is_featured=is_featured,
        status=VideoStatus.PROCESSING,
        file_size=len(content)
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # 处理标签
    tag_names = []
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        for tag_name in tag_list:
            tag_result = await db.execute(select(DarkwebTag).where(DarkwebTag.name == tag_name))
            tag = tag_result.scalar_one_or_none()
            
            if not tag:
                tag = DarkwebTag(name=tag_name, use_count=0)
                db.add(tag)
                await db.flush()
            
            # 插入关联
            await db.execute(text(
                "INSERT INTO darkweb_video_tags_association (video_id, tag_id) VALUES (:video_id, :tag_id) ON CONFLICT DO NOTHING"
            ), {"video_id": video.id, "tag_id": tag.id})
            
            tag.use_count += 1
            tag_names.append(tag_name)
        
        await db.commit()
    
    # 处理自定义封面
    if custom_cover_url:
        darkweb_thumb_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_thumbnails")
        os.makedirs(darkweb_thumb_dir, exist_ok=True)
        
        temp_cover_path = custom_cover_url.replace("/uploads/", settings.UPLOAD_DIR + "/")
        if os.path.exists(temp_cover_path):
            final_cover_path = os.path.join(darkweb_thumb_dir, f"{video.id}.jpg")
            shutil.copy(temp_cover_path, final_cover_path)
            video.cover_url = f"/uploads/darkweb_thumbnails/{video.id}.jpg"
            await db.commit()
    
    # 后台处理视频
    background_tasks.add_task(
        process_darkweb_video,
        video.id,
        file_path,
        bool(custom_cover_url)
    )
    
    return VideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        cover_url=video.cover_url,
        hls_url=video.hls_url,
        preview_url=video.preview_url,
        duration=video.duration,
        status=video.status.value if video.status else "PROCESSING",
        view_count=video.view_count or 0,
        like_count=video.like_count or 0,
        category_id=video.category_id,
        category_name=None,
        tags=tag_names,
        is_featured=video.is_featured,
        created_at=video.created_at
    )


async def process_darkweb_video(video_id: int, file_path: str, skip_thumbnail: bool = False):
    """后台处理暗网视频"""
    import asyncio
    import subprocess
    from app.core.database import AsyncSessionLocal
    from app.services.video_processor import VideoProcessor
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(DarkwebVideo).where(DarkwebVideo.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return
            
            print(f"[Darkweb] Processing video {video_id}...")
            
            # 1. 获取视频信息
            video_info = await VideoProcessor.get_video_info(file_path)
            video.duration = video_info.get("duration", 0)
            
            # 2. 生成缩略图
            if not skip_thumbnail:
                darkweb_thumb_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_thumbnails")
                os.makedirs(darkweb_thumb_dir, exist_ok=True)
                
                # 选择合适的时间点
                seek_time = min(video.duration * 0.3, 10) if video.duration > 0 else 5
                thumbnail_path = os.path.join(darkweb_thumb_dir, f"{video_id}.webp")
                
                cmd = [
                    "ffmpeg", "-ss", str(seek_time), "-i", file_path,
                    "-vframes", "1", "-q:v", "2", "-vf", "scale=640:-1",
                    "-y", thumbnail_path
                ]
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, timeout=60))
                
                if os.path.exists(thumbnail_path):
                    video.cover_url = f"/uploads/darkweb_thumbnails/{video_id}.webp"
                    print(f"[Darkweb] Video {video_id} thumbnail generated")
            
            # 3. 生成预览视频
            darkweb_preview_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_previews")
            os.makedirs(darkweb_preview_dir, exist_ok=True)
            
            preview_duration = min(10, video.duration * 0.1) if video.duration > 0 else 5
            preview_start = min(video.duration * 0.2, 5) if video.duration > 0 else 0
            preview_path = os.path.join(darkweb_preview_dir, f"{video_id}.mp4")
            
            cmd = [
                "ffmpeg", "-ss", str(preview_start), "-i", file_path,
                "-t", str(preview_duration), "-vf", "scale=480:-1",
                "-c:v", "libx264", "-preset", "fast", "-crf", "28",
                "-an", "-y", preview_path
            ]
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, timeout=120))
            
            if os.path.exists(preview_path):
                video.preview_url = f"/uploads/darkweb_previews/{video_id}.mp4"
            
            # 4. 转码为HLS
            darkweb_hls_dir = os.path.join(settings.UPLOAD_DIR, "darkweb_hls", str(video_id))
            os.makedirs(darkweb_hls_dir, exist_ok=True)
            
            hls_output = os.path.join(darkweb_hls_dir, "playlist.m3u8")
            cmd = [
                "ffmpeg", "-i", file_path,
                "-c:v", "libx264", "-c:a", "aac",
                "-preset", "fast", "-crf", "22",
                "-hls_time", "10", "-hls_list_size", "0",
                "-hls_segment_filename", os.path.join(darkweb_hls_dir, "segment_%03d.ts"),
                "-y", hls_output
            ]
            
            print(f"[Darkweb] Transcoding video {video_id}...")
            await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True, timeout=3600))
            
            if os.path.exists(hls_output):
                video.hls_url = f"/uploads/darkweb_hls/{video_id}/playlist.m3u8"
            
            video.status = VideoStatus.PUBLISHED
            video.published_at = datetime.utcnow()
            
            await db.commit()
            print(f"[Darkweb] Video {video_id} processed successfully")
            
        except Exception as e:
            import traceback
            print(f"[Darkweb] Error processing video {video_id}: {e}")
            print(traceback.format_exc())
            # 标记为失败
            try:
                result = await db.execute(select(DarkwebVideo).where(DarkwebVideo.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.status = VideoStatus.FAILED
                    await db.commit()
            except:
                pass


# ========== 转码服务器专用API ==========
from fastapi import Header
from app.core.config import settings

TRANSCODE_SECRET_KEY = getattr(settings, 'TRANSCODE_SECRET_KEY', 'vYTWoms4FKOqySca1jCLtNHRVz3BAI6U')


@router.get("/transcode/categories")
async def get_categories_for_transcode(
    x_transcode_key: str = Header(None, alias="X-Transcode-Key"),
    db: AsyncSession = Depends(get_db)
):
    """转码服务器获取暗网分类（无需登录，使用密钥验证）"""
    if x_transcode_key != TRANSCODE_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid transcode key")
    
    result = await db.execute(
        select(DarkwebCategory).order_by(DarkwebCategory.level, DarkwebCategory.sort_order)
    )
    all_categories = result.scalars().all()
    
    count_result = await db.execute(
        select(DarkwebVideo.category_id, func.count(DarkwebVideo.id))
        .group_by(DarkwebVideo.category_id)
    )
    count_map = {r[0]: r[1] for r in count_result.fetchall()}
    
    parent_categories = [c for c in all_categories if c.level == 1]
    child_categories = [c for c in all_categories if c.level == 2]
    
    children_map = {}
    for child in child_categories:
        if child.parent_id not in children_map:
            children_map[child.parent_id] = []
        child_resp = {
            "id": child.id,
            "name": child.name,
            "description": child.description,
            "icon": child.icon,
            "sort_order": child.sort_order or 0,
            "is_active": child.is_active if child.is_active is not None else True,
            "parent_id": child.parent_id,
            "level": child.level or 2,
            "video_count": count_map.get(child.id, 0),
            "children": []
        }
        children_map[child.parent_id].append(child_resp)
    
    categories = []
    for parent in parent_categories:
        children = children_map.get(parent.id, [])
        total_count = count_map.get(parent.id, 0) + sum(c["video_count"] for c in children)
        cat = {
            "id": parent.id,
            "name": parent.name,
            "description": parent.description,
            "icon": parent.icon,
            "sort_order": parent.sort_order or 0,
            "is_active": parent.is_active if parent.is_active is not None else True,
            "parent_id": parent.parent_id,
            "level": parent.level or 1,
            "video_count": total_count,
            "children": children
        }
        categories.append(cat)
    
    return categories


@router.get("/transcode/tags")
async def get_tags_for_transcode(
    x_transcode_key: str = Header(None, alias="X-Transcode-Key"),
    db: AsyncSession = Depends(get_db)
):
    """转码服务器获取暗网标签（无需登录，使用密钥验证）"""
    if x_transcode_key != TRANSCODE_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid transcode key")
    
    result = await db.execute(
        select(DarkwebTag)
        .order_by(DarkwebTag.use_count.desc())
        .limit(100)
    )
    tags = result.scalars().all()
    return {"items": [{"id": t.id, "name": t.name, "use_count": t.use_count or 0} for t in tags]}


# ========== 转码服务器专用API ==========

class TranscodeVideoCreate(BaseModel):
    """转码服务器创建暗网视频的请求体"""
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    hls_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: float = 0
    category_id: Optional[int] = None
    tags: Optional[List[int]] = None  # 标签ID列表
    is_featured: bool = False


@router.post("/transcode/videos")
async def create_video_from_transcode(
    data: TranscodeVideoCreate,
    x_transcode_key: str = Header(None, alias="X-Transcode-Key"),
    db: AsyncSession = Depends(get_db)
):
    """转码服务器创建暗网视频（无需登录，使用密钥验证）"""
    if x_transcode_key != TRANSCODE_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid transcode key")
    
    # 使用北京时间 (UTC+8)
    from datetime import datetime, timedelta
    beijing_now = datetime.utcnow() + timedelta(hours=8)
    
    # 创建视频记录
    video = DarkwebVideo(
        title=data.title,
        description=data.description,
        cover_url=data.cover_url,
        hls_url=data.hls_url,
        preview_url=data.preview_url,
        duration=data.duration,
        category_id=data.category_id,
        is_featured=data.is_featured,
        uploader_id=1,  # 使用管理员ID
        status=VideoStatus.PUBLISHED if data.hls_url else VideoStatus.UPLOADING,
        created_at=beijing_now,
        published_at=beijing_now if data.hls_url else None
    )
    
    # 处理标签（通过ID）
    if data.tags:
        for tag_id in data.tags:
            result = await db.execute(
                select(DarkwebTag).where(DarkwebTag.id == tag_id)
            )
            tag = result.scalar_one_or_none()
            if tag:
                tag.use_count = (tag.use_count or 0) + 1
                video.tags.append(tag)
    
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    return {
        "id": video.id,
        "title": video.title,
        "status": video.status.value if video.status else "PUBLISHED"
    }
