"""
首页聚合接口 - 减少前端请求数量，提升首屏加载速度
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel
import json
import logging

from app.core.database import get_db
from app.core.redis import RedisCache
from app.api.deps import get_current_user_optional
from app.models.user import User, UserVIP
from app.models.video import Video, VideoCategory, VideoStatus
from app.models.ad import IconAd, FuncEntry, Announcement
from app.models.content import Banner
from app.api.settings import load_settings
from app.services.cache_service import CacheService, CacheTTL

logger = logging.getLogger(__name__)

router = APIRouter()


# 默认图标广告数据
DEFAULT_ICON_ADS = [
    {"name": "AI女友", "icon": "🤖", "image": "", "link": "/ai-girlfriend"},
    {"name": "充值中心", "icon": "💰", "image": "", "link": "/recharge"},
]

# 默认功能入口
DEFAULT_FUNC_ENTRIES = [
    {"name": "VIP会员", "image": None, "link": "/vip"},
    {"name": "我的收藏", "image": None, "link": "/favorites"},
]


class VideoItem(BaseModel):
    id: int
    title: str
    cover_url: Optional[str] = None
    preview_url: Optional[str] = None
    duration: float = 0
    view_count: int = 0
    comment_count: int = 0
    is_vip_only: bool = False
    category_name: Optional[str] = None
    tags: List[str] = []

    class Config:
        from_attributes = True


class CategoryChild(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    is_featured: bool = False


class CategoryItem(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    is_featured: bool = False
    children: List[CategoryChild] = []


class IconAdItem(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None


class FuncEntryItem(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    link: Optional[str] = None


class AnnouncementItem(BaseModel):
    id: int
    content: str
    link: Optional[str] = None


class SiteSettingsItem(BaseModel):
    site_name: str = "Soul"
    logo: Optional[str] = None


class HomeInitResponse(BaseModel):
    """首页初始化数据聚合响应"""
    site_settings: SiteSettingsItem
    categories: List[CategoryItem]
    func_entries: List[FuncEntryItem]
    icon_ads: List[IconAdItem]
    videos: List[VideoItem]
    announcements: List[AnnouncementItem]
    banners: List[dict] = []  # 轮播图
    is_vip: bool = False
    cache_time: int = 300


# 缓存键
CACHE_KEY_HOME_STATIC = "home:static:data"
CACHE_TTL = 300  # 5分钟


@router.get("/banners")
async def get_public_banners(
    position: str = Query("home", description="显示位置: home/video/profile/vip"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开轮播图（用户端）- 带缓存
    只返回当前时间内有效的、已启用的轮播图
    """
    # 尝试从缓存获取
    cache_key = f"banners:{position}"
    cached = await CacheService.get(cache_key)
    if cached:
        # 异步更新展示次数（不阻塞响应）
        banner_ids = [b["id"] for b in cached]
        if banner_ids:
            await db.execute(
                Banner.__table__.update()
                .where(Banner.id.in_(banner_ids))
                .values(impression_count=Banner.impression_count + 1)
            )
            await db.commit()
        return cached
    
    now = datetime.utcnow()
    
    query = select(Banner).where(
        Banner.is_active == True,
        Banner.position == position
    )
    
    # 过滤时间范围
    query = query.where(
        (Banner.start_time == None) | (Banner.start_time <= now)
    )
    query = query.where(
        (Banner.end_time == None) | (Banner.end_time >= now)
    )
    
    query = query.order_by(Banner.sort_order.asc())
    
    result = await db.execute(query)
    banners = result.scalars().all()
    
    # 更新展示次数
    for b in banners:
        b.impression_count = (b.impression_count or 0) + 1
    await db.commit()
    
    data = [
        {
            "id": b.id,
            "title": b.title,
            "image_url": b.image_url,
            "link_url": b.link_url,
            "link_type": b.link_type or "none",
            "position": b.position
        }
        for b in banners
    ]
    
    # 缓存5分钟
    await CacheService.set(cache_key, data, CacheTTL.MEDIUM)
    
    return data


@router.get("/init", response_model=HomeInitResponse)
async def get_home_init(
    category_id: Optional[int] = Query(None, description="分类ID，0或不传表示推荐"),
    sort_by: str = Query("hot", description="排序方式: hot, created_at, view_count"),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    首页初始化聚合接口
    """
    try:
        # 检查用户VIP状态
        is_vip = False
        if current_user:
            result = await db.execute(
                select(UserVIP).where(
                    UserVIP.user_id == current_user.id,
                    UserVIP.is_active == True,
                    UserVIP.expire_date > datetime.utcnow()
                )
            )
            is_vip = result.scalar_one_or_none() is not None
        
        # 获取网站设置（同步函数）
        settings_data = load_settings()
        site_settings = SiteSettingsItem(
            site_name=settings_data.get("site_name", "Soul"),
            logo=settings_data.get("logo")
        )
        
        # 获取分类
        result = await db.execute(
            select(VideoCategory)
            .where(VideoCategory.parent_id == None)
            .order_by(VideoCategory.sort_order)
        )
        parent_categories = result.scalars().all()
        
        result = await db.execute(
            select(VideoCategory)
            .where(VideoCategory.parent_id != None)
            .order_by(VideoCategory.sort_order)
        )
        child_categories = result.scalars().all()
        
        categories = []
        for parent in parent_categories:
            children = [
                CategoryChild(
                    id=child.id,
                    name=child.name,
                    icon=child.icon,
                    is_featured=bool(child.is_featured) if hasattr(child, 'is_featured') and child.is_featured is not None else False
                )
                for child in child_categories
                if child.parent_id == parent.id
            ]
            categories.append(CategoryItem(
                id=parent.id,
                name=parent.name,
                icon=parent.icon,
                is_featured=bool(parent.is_featured) if hasattr(parent, 'is_featured') and parent.is_featured is not None else False,
                children=children
            ))
        
        # 获取功能入口
        result = await db.execute(
            select(FuncEntry)
            .where(FuncEntry.is_active == True)
            .order_by(FuncEntry.sort_order)
        )
        func_entries_db = result.scalars().all()
        
        func_entries = []
        if func_entries_db:
            for entry in func_entries_db:
                func_entries.append(FuncEntryItem(
                    id=entry.id,
                    name=entry.name,
                    image=entry.image,
                    link=entry.link
                ))
        else:
            for i, entry in enumerate(DEFAULT_FUNC_ENTRIES):
                func_entries.append(FuncEntryItem(
                    id=i+1,
                    name=entry["name"],
                    image=entry.get("image"),
                    link=entry["link"]
                ))
        
        # 获取图标广告（VIP用户不显示）
        icon_ads = []
        if not is_vip:
            result = await db.execute(
                select(IconAd)
                .where(IconAd.is_active == True)
                .order_by(IconAd.sort_order, IconAd.id)
            )
            ads_db = result.scalars().all()
            
            if ads_db:
                for ad in ads_db:
                    icon_ads.append(IconAdItem(
                        id=ad.id,
                        name=ad.name,
                        icon=ad.icon,
                        image=ad.image,
                        link=ad.link
                    ))
            else:
                for i, ad in enumerate(DEFAULT_ICON_ADS):
                    icon_ads.append(IconAdItem(
                        id=i+1,
                        name=ad["name"],
                        icon=ad["icon"],
                        image=ad.get("image"),
                        link=ad["link"]
                    ))
        
        # 获取公告
        result = await db.execute(
            select(Announcement)
            .where(Announcement.is_active == True)
            .order_by(Announcement.sort_order.desc())
            .limit(5)
        )
        announcements_db = result.scalars().all()
        
        announcements = []
        for ann in announcements_db:
            announcements.append(AnnouncementItem(
                id=ann.id,
                content=ann.content,
                link=ann.link
            ))
        
        # 获取轮播图
        now = datetime.utcnow()
        banner_query = select(Banner).where(
            Banner.is_active == True,
            Banner.position == "home"
        )
        banner_query = banner_query.where(
            (Banner.start_time == None) | (Banner.start_time <= now)
        )
        banner_query = banner_query.where(
            (Banner.end_time == None) | (Banner.end_time >= now)
        )
        banner_query = banner_query.order_by(Banner.sort_order.asc())
        
        result = await db.execute(banner_query)
        banners_db = result.scalars().all()
        
        banners = [
            {
                "id": b.id,
                "title": b.title,
                "image_url": b.image_url,
                "link_url": b.link_url,
                "link_type": b.link_type or "none",
                "position": b.position
            }
            for b in banners_db
        ]
        
        # 获取视频列表（排除短视频）
        query = select(Video).where(
            Video.status == VideoStatus.PUBLISHED,
            Video.is_short != True  # 排除短视频
        )
        
        if category_id and category_id > 0:
            query = query.where(Video.category_id == category_id)
        
        if sort_by == "created_at":
            query = query.order_by(Video.created_at.desc())
        elif sort_by == "view_count":
            query = query.order_by(Video.view_count.desc())
        else:
            query = query.order_by(Video.view_count.desc(), Video.created_at.desc())
        
        query = query.options(selectinload(Video.category)).limit(limit)
        
        result = await db.execute(query)
        videos_db = result.scalars().all()
        
        videos = []
        for video in videos_db:
            videos.append(VideoItem(
                id=video.id,
                title=video.title,
                cover_url=video.cover_url,
                preview_url=video.preview_url,
                duration=video.duration or 0,
                view_count=video.view_count or 0,
                comment_count=video.comment_count or 0,
                is_vip_only=video.is_vip_only if hasattr(video, 'is_vip_only') else False,
                category_name=video.category.name if video.category else None,
                tags=[]
            ))
        
        return HomeInitResponse(
            site_settings=site_settings,
            categories=categories,
            func_entries=func_entries,
            icon_ads=icon_ads,
            videos=videos,
            announcements=announcements,
            banners=banners,
            is_vip=is_vip,
            cache_time=CACHE_TTL
        )
        
    except Exception as e:
        logger.error(f"首页聚合接口错误: {str(e)}", exc_info=True)
        raise


@router.get("/videos")
async def get_home_videos(
    category_id: Optional[int] = Query(None),
    sort_by: str = Query("hot"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    获取更多视频（分页加载用，排除短视频）
    """
    offset = (page - 1) * limit
    
    query = select(Video).where(
        Video.status == VideoStatus.PUBLISHED,
        Video.is_short != True  # 排除短视频
    )
    
    if category_id and category_id > 0:
        query = query.where(Video.category_id == category_id)
    
    if sort_by == "created_at":
        query = query.order_by(Video.created_at.desc())
    elif sort_by == "view_count":
        query = query.order_by(Video.view_count.desc())
    else:
        query = query.order_by(Video.view_count.desc(), Video.created_at.desc())
    
    query = query.options(selectinload(Video.category)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    videos_db = result.scalars().all()
    
    return {
        "videos": [
            {
                "id": video.id,
                "title": video.title,
                "cover_url": video.cover_url,
                "preview_url": video.preview_url,
                "duration": video.duration or 0,
                "view_count": video.view_count or 0,
                "comment_count": video.comment_count or 0,
                "is_vip_only": video.is_vip_only if hasattr(video, 'is_vip_only') else False,
                "category_name": video.category.name if video.category else None
            }
            for video in videos_db
        ],
        "page": page,
        "limit": limit,
        "has_more": len(videos_db) == limit
    }

















