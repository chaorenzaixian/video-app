"""
暗网视频专区API
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.models.user import User, UserVIP
from app.models.darkweb import DarkwebCategory, DarkwebTag, DarkwebVideo, DarkwebView
from app.models.video import VideoStatus
from app.models.system_config import SystemConfig

router = APIRouter(prefix="/darkweb", tags=["暗网视频"])


# ========== Schemas ==========
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[int] = None
    level: int = 1
    children: List["CategoryResponse"] = []
    
    class Config:
        from_attributes = True

CategoryResponse.model_rebuild()


class TagResponse(BaseModel):
    id: int
    name: str
    use_count: int = 0
    
    class Config:
        from_attributes = True


class VideoListItem(BaseModel):
    id: int
    title: str
    cover_url: Optional[str] = None
    duration: float = 0
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    category_name: Optional[str] = None
    tags: List[str] = []
    is_featured: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoDetail(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    hls_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: float = 0
    view_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tags: List[str] = []
    uploader_id: int
    uploader_name: str = ""
    uploader_avatar: Optional[str] = None
    is_featured: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    items: List[VideoListItem]
    total: int
    page: int
    page_size: int


# ========== 辅助函数 ==========
async def get_darkweb_min_vip_level(db: AsyncSession) -> int:
    """获取暗网专区最低VIP等级要求"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "darkweb_min_vip_level")
    )
    config = result.scalar_one_or_none()
    if config:
        return int(config.value)
    return 5  # 默认黄金至尊(5)


async def check_darkweb_access(db: AsyncSession, user: User) -> bool:
    """检查用户是否有权访问暗网专区"""
    min_level = await get_darkweb_min_vip_level(db)
    
    # 如果最低等级要求是0，所有人都可以访问
    if min_level == 0:
        return True
    
    if not user:
        return False
    
    # 获取用户VIP等级
    result = await db.execute(
        select(UserVIP).where(
            UserVIP.user_id == user.id,
            UserVIP.is_active == True
        )
    )
    user_vip = result.scalar_one_or_none()
    
    if not user_vip:
        return False
    
    user_level = user_vip.vip_level or 0
    
    return user_level >= min_level


# ========== 用户端API ==========
@router.get("/access-check")
async def check_access(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """检查用户是否有权访问暗网专区"""
    min_level = await get_darkweb_min_vip_level(db)
    
    if not current_user:
        return {
            "has_access": False,
            "min_vip_level": min_level,
            "user_vip_level": 0
        }
    
    has_access = await check_darkweb_access(db, current_user)
    
    # 获取用户当前VIP等级
    result = await db.execute(
        select(UserVIP).where(UserVIP.user_id == current_user.id, UserVIP.is_active == True)
    )
    user_vip = result.scalar_one_or_none()
    user_level = user_vip.vip_level if user_vip else 0
    
    return {
        "has_access": has_access,
        "min_vip_level": min_level,
        "user_vip_level": user_level
    }


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取暗网分类列表（带层级）- 公开接口"""
    # 获取所有一级分类
    result = await db.execute(
        select(DarkwebCategory).where(
            DarkwebCategory.is_active == True,
            DarkwebCategory.level == 1
        ).order_by(DarkwebCategory.sort_order)
    )
    parent_categories = result.scalars().all()
    
    # 获取所有二级分类
    result = await db.execute(
        select(DarkwebCategory).where(
            DarkwebCategory.is_active == True,
            DarkwebCategory.level == 2
        ).order_by(DarkwebCategory.sort_order)
    )
    child_categories = result.scalars().all()
    
    # 构建层级结构 - 手动创建响应对象避免懒加载问题
    children_map = {}
    for child in child_categories:
        if child.parent_id not in children_map:
            children_map[child.parent_id] = []
        children_map[child.parent_id].append(CategoryResponse(
            id=child.id,
            name=child.name,
            description=child.description,
            icon=child.icon,
            sort_order=child.sort_order or 0,
            parent_id=child.parent_id,
            level=child.level or 2,
            children=[]
        ))
    
    categories = []
    for parent in parent_categories:
        cat = CategoryResponse(
            id=parent.id,
            name=parent.name,
            description=parent.description,
            icon=parent.icon,
            sort_order=parent.sort_order or 0,
            parent_id=parent.parent_id,
            level=parent.level or 1,
            children=children_map.get(parent.id, [])
        )
        categories.append(cat)
    
    return categories


@router.get("/tags", response_model=List[TagResponse])
async def get_tags(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取热门标签"""
    if not await check_darkweb_access(db, current_user):
        raise HTTPException(status_code=403, detail="VIP等级不足")
    
    result = await db.execute(
        select(DarkwebTag).order_by(DarkwebTag.use_count.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/videos", response_model=VideoListResponse)
async def get_videos(
    category_id: Optional[int] = None,
    tag: Optional[str] = None,
    keyword: Optional[str] = None,
    sort: str = Query("latest", regex="^(latest|popular|views|random)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取暗网视频列表 - 公开接口，所有人可浏览"""
    # 基础查询
    query = select(DarkwebVideo).where(DarkwebVideo.status == VideoStatus.PUBLISHED)
    count_query = select(func.count(DarkwebVideo.id)).where(DarkwebVideo.status == VideoStatus.PUBLISHED)
    
    # 分类筛选（支持一级分类查询所有子分类）
    if category_id:
        # 检查是否是一级分类
        cat_result = await db.execute(
            select(DarkwebCategory).where(DarkwebCategory.id == category_id)
        )
        category = cat_result.scalar_one_or_none()
        
        if category and category.level == 1:
            # 获取所有子分类ID
            sub_result = await db.execute(
                select(DarkwebCategory.id).where(DarkwebCategory.parent_id == category_id)
            )
            sub_ids = [r[0] for r in sub_result.fetchall()]
            sub_ids.append(category_id)
            query = query.where(DarkwebVideo.category_id.in_(sub_ids))
            count_query = count_query.where(DarkwebVideo.category_id.in_(sub_ids))
        else:
            query = query.where(DarkwebVideo.category_id == category_id)
            count_query = count_query.where(DarkwebVideo.category_id == category_id)
    
    # 关键词搜索
    if keyword:
        query = query.where(DarkwebVideo.title.ilike(f"%{keyword}%"))
        count_query = count_query.where(DarkwebVideo.title.ilike(f"%{keyword}%"))
    
    # 标签筛选
    if tag:
        query = query.join(DarkwebVideo.tags).where(DarkwebTag.name == tag)
        count_query = count_query.join(DarkwebVideo.tags).where(DarkwebTag.name == tag)
    
    # 排序
    if sort == "latest":
        query = query.order_by(DarkwebVideo.created_at.desc())
    elif sort == "popular":
        query = query.order_by(DarkwebVideo.like_count.desc())
    elif sort == "views":
        query = query.order_by(DarkwebVideo.view_count.desc())
    elif sort == "random":
        query = query.order_by(func.random())
    
    # 总数
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.options(selectinload(DarkwebVideo.category), selectinload(DarkwebVideo.tags))
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    items = []
    for v in videos:
        items.append(VideoListItem(
            id=v.id,
            title=v.title,
            cover_url=v.cover_url,
            duration=v.duration,
            view_count=v.view_count,
            like_count=v.like_count,
            comment_count=v.comment_count,
            category_name=v.category.name if v.category else None,
            tags=[t.name for t in v.tags] if v.tags else [],
            is_featured=v.is_featured,
            created_at=v.created_at
        ))
    
    return VideoListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/videos/{video_id}", response_model=VideoDetail)
async def get_video_detail(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取暗网视频详情"""
    if not await check_darkweb_access(db, current_user):
        raise HTTPException(status_code=403, detail="VIP等级不足，无法访问暗网专区")
    
    result = await db.execute(
        select(DarkwebVideo)
        .options(selectinload(DarkwebVideo.category), selectinload(DarkwebVideo.tags), selectinload(DarkwebVideo.uploader))
        .where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 增加观看次数
    video.view_count += 1
    await db.commit()
    
    # 记录观看
    view = DarkwebView(video_id=video_id, user_id=current_user.id)
    db.add(view)
    await db.commit()
    
    return VideoDetail(
        id=video.id,
        title=video.title,
        description=video.description,
        cover_url=video.cover_url,
        hls_url=video.hls_url,
        preview_url=video.preview_url,
        duration=video.duration,
        view_count=video.view_count,
        like_count=video.like_count,
        favorite_count=video.favorite_count,
        comment_count=video.comment_count,
        category_id=video.category_id,
        category_name=video.category.name if video.category else None,
        tags=[t.name for t in video.tags],
        uploader_id=video.uploader_id,
        uploader_name=video.uploader.nickname if video.uploader else "",
        uploader_avatar=video.uploader.avatar if video.uploader else None,
        is_featured=video.is_featured,
        created_at=video.created_at
    )


@router.get("/recommend", response_model=List[VideoListItem])
async def get_recommend_videos(
    exclude_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取推荐视频"""
    if not await check_darkweb_access(db, current_user):
        raise HTTPException(status_code=403, detail="VIP等级不足")
    
    query = select(DarkwebVideo).where(DarkwebVideo.status == VideoStatus.PUBLISHED)
    
    if exclude_id:
        query = query.where(DarkwebVideo.id != exclude_id)
    
    # 优先推荐精选，然后按观看量排序
    query = query.order_by(DarkwebVideo.is_featured.desc(), DarkwebVideo.view_count.desc()).limit(limit)
    query = query.options(selectinload(DarkwebVideo.category))
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return [VideoListItem(
        id=v.id,
        title=v.title,
        cover_url=v.cover_url,
        duration=v.duration,
        view_count=v.view_count,
        like_count=v.like_count,
        comment_count=v.comment_count,
        category_name=v.category.name if v.category else None,
        is_featured=v.is_featured,
        created_at=v.created_at
    ) for v in videos]


# ========== 点赞、收藏、评论 ==========
@router.post("/videos/{video_id}/like")
async def like_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """点赞/取消点赞视频"""
    if not await check_darkweb_access(db, current_user):
        raise HTTPException(status_code=403, detail="VIP等级不足")
    
    result = await db.execute(
        select(DarkwebVideo).where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 简单实现：直接增加点赞数
    video.like_count = (video.like_count or 0) + 1
    await db.commit()
    
    return {"liked": True, "like_count": video.like_count}


@router.post("/videos/{video_id}/favorite")
async def favorite_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """收藏/取消收藏视频"""
    if not await check_darkweb_access(db, current_user):
        raise HTTPException(status_code=403, detail="VIP等级不足")
    
    result = await db.execute(
        select(DarkwebVideo).where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video.favorite_count = (video.favorite_count or 0) + 1
    await db.commit()
    
    return {"favorited": True, "favorite_count": video.favorite_count}


@router.post("/videos/{video_id}/view")
async def record_view(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """记录观看"""
    result = await db.execute(
        select(DarkwebVideo).where(DarkwebVideo.id == video_id)
    )
    video = result.scalar_one_or_none()
    if video:
        video.view_count = (video.view_count or 0) + 1
        await db.commit()
    
    return {"success": True}
