"""
首页聚合接口 - 减少前端请求数量，提升首屏加载速度
优化：静态数据缓存、分类查询合并
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel
from collections import defaultdict
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

# 缓存键定义
CACHE_KEY_CATEGORIES = "home:categories"
CACHE_KEY_FUNC_ENTRIES = "home:func_entries"
CACHE_KEY_ICON_ADS = "home:icon_ads"
CACHE_KEY_ANNOUNCEMENTS = "home:announcements"
CACHE_KEY_SITE_SETTINGS = "home:site_settings"


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


# 缓存TTL
CACHE_TTL = 300  # 5分钟


# ========== 缓存辅助函数 ==========

async def get_cached_categories(db: AsyncSession) -> List[dict]:
    """获取分类数据（带缓存）- 优化：单次查询 + 内存分组"""
    cached = await CacheService.get(CACHE_KEY_CATEGORIES)
    if cached:
        return cached
    
    # 单次查询所有分类
    result = await db.execute(
        select(VideoCategory).order_by(VideoCategory.sort_order)
    )
    all_categories = result.scalars().all()
    
    # 内存中分组
    parents = []
    children_map = defaultdict(list)
    
    for cat in all_categories:
        cat_data = {
            "id": cat.id,
            "name": cat.name,
            "icon": cat.icon,
            "is_featured": bool(cat.is_featured) if hasattr(cat, 'is_featured') and cat.is_featured is not None else False,
            "parent_id": cat.parent_id
        }
        if cat.parent_id is None:
            parents.append(cat_data)
        else:
            children_map[cat.parent_id].append(cat_data)
    
    # 组装树形结构
    categories = []
    for parent in parents:
        parent["children"] = children_map.get(parent["id"], [])
        del parent["parent_id"]
        for child in parent["children"]:
            del child["parent_id"]
        categories.append(parent)
    
    await CacheService.set(CACHE_KEY_CATEGORIES, categories, CacheTTL.LONG)
    return categories


async def get_cached_func_entries(db: AsyncSession) -> List[dict]:
    """获取功能入口（带缓存）"""
    cached = await CacheService.get(CACHE_KEY_FUNC_ENTRIES)
    if cached:
        return cached
    
    result = await db.execute(
        select(FuncEntry)
        .where(FuncEntry.is_active == True)
        .order_by(FuncEntry.sort_order)
    )
    entries_db = result.scalars().all()
    
    if entries_db:
        entries = [
            {"id": e.id, "name": e.name, "image": e.image, "link": e.link}
            for e in entries_db
        ]
    else:
        entries = [
            {"id": i+1, "name": e["name"], "image": e.get("image"), "link": e["link"]}
            for i, e in enumerate(DEFAULT_FUNC_ENTRIES)
        ]
    
    await CacheService.set(CACHE_KEY_FUNC_ENTRIES, entries, CacheTTL.LONG)
    return entries


async def get_cached_icon_ads(db: AsyncSession) -> List[dict]:
    """获取图标广告（带缓存）"""
    cached = await CacheService.get(CACHE_KEY_ICON_ADS)
    if cached:
        return cached
    
    result = await db.execute(
        select(IconAd)
        .where(IconAd.is_active == True)
        .order_by(IconAd.sort_order, IconAd.id)
    )
    ads_db = result.scalars().all()
    
    if ads_db:
        ads = [
            {"id": a.id, "name": a.name, "icon": a.icon, "image": a.image, "link": a.link}
            for a in ads_db
        ]
    else:
        ads = [
            {"id": i+1, "name": a["name"], "icon": a["icon"], "image": a.get("image"), "link": a["link"]}
            for i, a in enumerate(DEFAULT_ICON_ADS)
        ]
    
    await CacheService.set(CACHE_KEY_ICON_ADS, ads, CacheTTL.MEDIUM)
    return ads


async def get_cached_announcements(db: AsyncSession) -> List[dict]:
    """获取公告（带缓存）"""
    cached = await CacheService.get(CACHE_KEY_ANNOUNCEMENTS)
    if cached:
        return cached
    
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active == True)
        .order_by(Announcement.sort_order.desc())
        .limit(5)
    )
    announcements_db = result.scalars().all()
    
    announcements = [
        {"id": a.id, "content": a.content, "link": a.link}
        for a in announcements_db
    ]
    
    await CacheService.set(CACHE_KEY_ANNOUNCEMENTS, announcements, CacheTTL.MEDIUM)
    return announcements


async def get_cached_site_settings() -> dict:
    """获取网站设置（带缓存）"""
    cached = await CacheService.get(CACHE_KEY_SITE_SETTINGS)
    if cached:
        return cached
    
    settings_data = load_settings()
    site_settings = {
        "site_name": settings_data.get("site_name", "Soul"),
        "logo": settings_data.get("logo")
    }
    
    await CacheService.set(CACHE_KEY_SITE_SETTINGS, site_settings, CacheTTL.LONG)
    return site_settings


async def get_cached_banners(db: AsyncSession, position: str = "home") -> List[dict]:
    """获取轮播图（带缓存）"""
    cache_key = f"banners:{position}"
    cached = await CacheService.get(cache_key)
    if cached:
        return cached
    
    now = datetime.utcnow()
    query = select(Banner).where(
        Banner.is_active == True,
        Banner.position == position
    )
    query = query.where(
        (Banner.start_time == None) | (Banner.start_time <= now)
    )
    query = query.where(
        (Banner.end_time == None) | (Banner.end_time >= now)
    )
    query = query.order_by(Banner.sort_order.asc())
    
    result = await db.execute(query)
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
    
    await CacheService.set(cache_key, banners, CacheTTL.MEDIUM)
    return banners


# ========== API 路由 ==========

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
    首页初始化聚合接口（优化版：缓存优先 + 安全并行）
    
    策略：
    1. 先并行获取所有缓存数据（不需要db）
    2. 缓存未命中的数据顺序查询（避免session并发问题）
    """
    import asyncio
    from app.core.database import AsyncSessionLocal
    
    try:
        # ========== 第一阶段：并行获取缓存数据（无db依赖） ==========
        async def get_cached_only(key: str):
            """仅从缓存获取，不查数据库"""
            return await CacheService.get(key)
        
        # 并行检查所有缓存
        (
            cached_site_settings,
            cached_categories,
            cached_func_entries,
            cached_icon_ads,
            cached_announcements,
            cached_banners,
            cached_videos
        ) = await asyncio.gather(
            get_cached_only(CACHE_KEY_SITE_SETTINGS),
            get_cached_only(CACHE_KEY_CATEGORIES),
            get_cached_only(CACHE_KEY_FUNC_ENTRIES),
            get_cached_only(CACHE_KEY_ICON_ADS),
            get_cached_only(CACHE_KEY_ANNOUNCEMENTS),
            get_cached_only("banners:home"),
            get_cached_only(f"home:videos:{category_id or 'all'}:{sort_by}:{limit}")
        )
        
        # ========== 第二阶段：顺序获取缓存未命中的数据 ==========
        # 使用传入的db session顺序执行，避免并发问题
        
        # VIP状态
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
        
        # 网站设置
        if cached_site_settings:
            site_settings_data = cached_site_settings
        else:
            site_settings_data = await get_cached_site_settings()
        
        # 分类
        if cached_categories:
            categories_data = cached_categories
        else:
            categories_data = await get_cached_categories(db)
        
        # 功能入口
        if cached_func_entries:
            func_entries_data = cached_func_entries
        else:
            func_entries_data = await get_cached_func_entries(db)
        
        # 图标广告
        if cached_icon_ads:
            icon_ads_data = cached_icon_ads
        else:
            icon_ads_data = await get_cached_icon_ads(db)
        
        # 公告
        if cached_announcements:
            announcements_data = cached_announcements
        else:
            announcements_data = await get_cached_announcements(db)
        
        # 轮播图
        if cached_banners:
            banners = cached_banners
        else:
            banners = await get_cached_banners(db, "home")
        
        # 视频列表
        if cached_videos:
            videos_data = cached_videos
        else:
            video_cache_key = f"home:videos:{category_id or 'all'}:{sort_by}:{limit}"
            
            query = select(Video).where(
                Video.status == VideoStatus.PUBLISHED,
                Video.is_short != True
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
            
            videos_data = [
                {
                    "id": v.id,
                    "title": v.title,
                    "cover_url": v.cover_url,
                    "preview_url": v.preview_url,
                    "duration": v.duration or 0,
                    "view_count": v.view_count or 0,
                    "comment_count": v.comment_count or 0,
                    "is_vip_only": v.is_vip_only if hasattr(v, 'is_vip_only') else False,
                    "category_name": v.category.name if v.category else None,
                    "tags": []
                }
                for v in videos_db
            ]
            
            await CacheService.set(video_cache_key, videos_data, CacheTTL.SHORT)
        
        # 构建响应
        site_settings = SiteSettingsItem(**site_settings_data)
        
        categories = [
            CategoryItem(
                id=c["id"],
                name=c["name"],
                icon=c.get("icon"),
                is_featured=c.get("is_featured", False),
                children=[CategoryChild(**child) for child in c.get("children", [])]
            )
            for c in categories_data
        ]
        
        func_entries = [FuncEntryItem(**e) for e in func_entries_data]
        
        # VIP用户不显示图标广告
        icon_ads = []
        if not is_vip:
            icon_ads = [IconAdItem(**a) for a in icon_ads_data]
        
        announcements = [AnnouncementItem(**a) for a in announcements_data]
        videos = [VideoItem(**v) for v in videos_data]
        
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


# ========== 缓存管理 ==========

async def invalidate_home_cache(cache_type: str = "all"):
    """
    清除首页缓存
    cache_type: categories/func_entries/icon_ads/announcements/banners/videos/all
    """
    if cache_type in ("categories", "all"):
        await CacheService.delete(CACHE_KEY_CATEGORIES)
    if cache_type in ("func_entries", "all"):
        await CacheService.delete(CACHE_KEY_FUNC_ENTRIES)
    if cache_type in ("icon_ads", "all"):
        await CacheService.delete(CACHE_KEY_ICON_ADS)
    if cache_type in ("announcements", "all"):
        await CacheService.delete(CACHE_KEY_ANNOUNCEMENTS)
    if cache_type in ("site_settings", "all"):
        await CacheService.delete(CACHE_KEY_SITE_SETTINGS)
    if cache_type in ("banners", "all"):
        await CacheService.delete_pattern("banners:*")
    if cache_type in ("videos", "all"):
        await CacheService.delete_pattern("home:videos:*")

















