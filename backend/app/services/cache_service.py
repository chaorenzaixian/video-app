"""
缓存服务 - 提供高性能数据缓存
"""
import json
from typing import Optional, List, Any, Callable
from functools import wraps
from datetime import datetime
import hashlib

from app.core.redis import RedisCache


class CacheKeys:
    """缓存键定义"""
    # 视频相关
    VIDEO_LIST = "video:list:{category}:{page}:{size}:{sort}"
    VIDEO_DETAIL = "video:detail:{id}"
    VIDEO_HOT = "video:hot:{period}"  # period: day, week, month
    
    # 分类相关
    CATEGORIES = "categories:all"
    CATEGORY_VIDEOS = "category:{id}:videos:{page}"
    
    # 用户相关
    USER_INFO = "user:info:{id}"
    USER_VIP = "user:vip:{id}"
    
    # 首页数据
    HOME_BANNERS = "home:banners"
    HOME_ANNOUNCEMENTS = "home:announcements"
    HOME_RECOMMEND = "home:recommend:{page}"
    
    # 统计数据
    STATS_OVERVIEW = "stats:overview"
    STATS_TODAY = "stats:today"
    
    # 社区相关
    COMMUNITY_POSTS = "community:posts:{feed_type}:{topic_id}:{page}"
    COMMUNITY_POST_DETAIL = "community:post:{id}"
    COMMUNITY_COMMENTS = "community:comments:{post_id}:{page}"
    COMMUNITY_TOPICS = "community:topics:{page}"
    COMMUNITY_TOPICS_RECOMMENDED = "community:topics:recommended"
    COMMUNITY_TOPICS_CATEGORIES = "community:topics:categories"


class CacheTTL:
    """缓存过期时间（秒）"""
    SHORT = 60          # 1分钟 - 实时性要求高的数据
    MEDIUM = 300        # 5分钟 - 一般数据
    LONG = 1800         # 30分钟 - 变化不频繁的数据
    VERY_LONG = 3600    # 1小时 - 基本不变的数据
    DAY = 86400         # 1天 - 静态数据


class CacheService:
    """缓存服务"""
    
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """获取缓存数据"""
        data = await RedisCache.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = CacheTTL.MEDIUM) -> bool:
        """设置缓存数据"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        return await RedisCache.set(key, value, ttl)
    
    @staticmethod
    async def delete(key: str) -> bool:
        """删除缓存"""
        return await RedisCache.delete(key)
    
    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """删除匹配模式的缓存（使用 SCAN + DEL）"""
        from app.core.redis import RedisCache
        
        count = 0
        try:
            redis = await RedisCache.get_client()
            if redis is None:
                return 0
            
            # 使用 SCAN 迭代查找匹配的键
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
        except Exception as e:
            print(f"[Cache] delete_pattern error: {e}")
        
        return count
    
    # ========== 视频缓存 ==========
    
    @staticmethod
    async def get_video_list(
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at"
    ) -> Optional[dict]:
        """获取视频列表缓存"""
        key = CacheKeys.VIDEO_LIST.format(
            category=category_id or "all",
            page=page,
            size=page_size,
            sort=sort_by
        )
        return await CacheService.get(key)
    
    @staticmethod
    async def set_video_list(
        data: dict,
        category_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at"
    ) -> bool:
        """设置视频列表缓存"""
        key = CacheKeys.VIDEO_LIST.format(
            category=category_id or "all",
            page=page,
            size=page_size,
            sort=sort_by
        )
        return await CacheService.set(key, data, CacheTTL.SHORT)
    
    @staticmethod
    async def get_video_detail(video_id: int) -> Optional[dict]:
        """获取视频详情缓存"""
        key = CacheKeys.VIDEO_DETAIL.format(id=video_id)
        return await CacheService.get(key)
    
    @staticmethod
    async def set_video_detail(video_id: int, data: dict) -> bool:
        """设置视频详情缓存"""
        key = CacheKeys.VIDEO_DETAIL.format(id=video_id)
        return await CacheService.set(key, data, CacheTTL.MEDIUM)
    
    @staticmethod
    async def invalidate_video(video_id: int) -> None:
        """使视频缓存失效"""
        key = CacheKeys.VIDEO_DETAIL.format(id=video_id)
        await CacheService.delete(key)
    
    # ========== 分类缓存 ==========
    
    @staticmethod
    async def get_categories() -> Optional[list]:
        """获取分类列表缓存"""
        return await CacheService.get(CacheKeys.CATEGORIES)
    
    @staticmethod
    async def set_categories(data: list) -> bool:
        """设置分类列表缓存"""
        return await CacheService.set(CacheKeys.CATEGORIES, data, CacheTTL.LONG)
    
    @staticmethod
    async def invalidate_categories() -> None:
        """使分类缓存失效"""
        await CacheService.delete(CacheKeys.CATEGORIES)
    
    # ========== 首页缓存 ==========
    
    @staticmethod
    async def get_home_banners() -> Optional[list]:
        """获取首页轮播图缓存"""
        return await CacheService.get(CacheKeys.HOME_BANNERS)
    
    @staticmethod
    async def set_home_banners(data: list) -> bool:
        """设置首页轮播图缓存"""
        return await CacheService.set(CacheKeys.HOME_BANNERS, data, CacheTTL.MEDIUM)
    
    @staticmethod
    async def get_home_announcements() -> Optional[list]:
        """获取首页公告缓存"""
        return await CacheService.get(CacheKeys.HOME_ANNOUNCEMENTS)
    
    @staticmethod
    async def set_home_announcements(data: list) -> bool:
        """设置首页公告缓存"""
        return await CacheService.set(CacheKeys.HOME_ANNOUNCEMENTS, data, CacheTTL.MEDIUM)
    
    # ========== 用户缓存 ==========
    
    @staticmethod
    async def get_user_vip(user_id: int) -> Optional[dict]:
        """获取用户VIP信息缓存"""
        key = CacheKeys.USER_VIP.format(id=user_id)
        return await CacheService.get(key)
    
    @staticmethod
    async def set_user_vip(user_id: int, data: dict) -> bool:
        """设置用户VIP信息缓存"""
        key = CacheKeys.USER_VIP.format(id=user_id)
        return await CacheService.set(key, data, CacheTTL.MEDIUM)
    
    @staticmethod
    async def invalidate_user_vip(user_id: int) -> None:
        """使用户VIP缓存失效"""
        key = CacheKeys.USER_VIP.format(id=user_id)
        await CacheService.delete(key)


def cached(key_template: str, ttl: int = CacheTTL.MEDIUM):
    """
    缓存装饰器
    
    用法:
    @cached("video:list:{category_id}:{page}", ttl=300)
    async def get_videos(category_id: int, page: int):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 构建缓存键
            cache_key = key_template.format(**kwargs)
            
            # 尝试从缓存获取
            cached_data = await CacheService.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                await CacheService.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_aside(
    key_template: str, 
    ttl: int = CacheTTL.MEDIUM,
    skip_none: bool = True
):
    """
    Cache-Aside 模式装饰器（增强版）
    
    特点:
    - 支持跳过None结果
    - 支持强制刷新缓存
    - 自动处理缓存失效
    
    用法:
    @cache_aside("user:vip:{user_id}", ttl=300)
    async def get_user_vip(user_id: int, force_refresh: bool = False):
        ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查是否强制刷新
            force_refresh = kwargs.pop('force_refresh', False)
            
            # 构建缓存键
            try:
                cache_key = key_template.format(**kwargs)
            except KeyError:
                # 如果模板参数不匹配，直接执行函数
                return await func(*args, **kwargs)
            
            # 非强制刷新时尝试从缓存获取
            if not force_refresh:
                cached_data = await CacheService.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 存入缓存（可选跳过None）
            if result is not None or not skip_none:
                await CacheService.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheInvalidator:
    """缓存失效管理器"""
    
    @staticmethod
    async def invalidate_video(video_id: int) -> None:
        """使视频相关缓存失效"""
        await CacheService.delete(CacheKeys.VIDEO_DETAIL.format(id=video_id))
        # 清除视频列表缓存
        await CacheService.delete_pattern("video:list:*")
        await CacheService.delete_pattern("home:recommend:*")
    
    @staticmethod
    async def invalidate_user(user_id: int) -> None:
        """使用户相关缓存失效"""
        await CacheService.delete(CacheKeys.USER_INFO.format(id=user_id))
        await CacheService.delete(CacheKeys.USER_VIP.format(id=user_id))
    
    @staticmethod
    async def invalidate_categories() -> None:
        """使分类缓存失效"""
        await CacheService.delete(CacheKeys.CATEGORIES)
        await CacheService.delete_pattern("category:*")
    
    @staticmethod
    async def invalidate_home() -> None:
        """使首页缓存失效"""
        await CacheService.delete(CacheKeys.HOME_BANNERS)
        await CacheService.delete(CacheKeys.HOME_ANNOUNCEMENTS)
        await CacheService.delete_pattern("home:recommend:*")
    
    @staticmethod
    async def invalidate_community(post_id: int = None) -> None:
        """使社区缓存失效"""
        if post_id:
            await CacheService.delete(CacheKeys.COMMUNITY_POST_DETAIL.format(id=post_id))
        await CacheService.delete_pattern("community:posts:*")
        await CacheService.delete_pattern("community:topics:*")
    
    @staticmethod
    async def invalidate_all() -> None:
        """清除所有缓存（谨慎使用）"""
        await CacheService.delete_pattern("*")


class CacheWarmer:
    """缓存预热器"""
    
    @staticmethod
    async def warm_categories(db) -> None:
        """预热分类缓存"""
        from app.models.video import Category
        from sqlalchemy import select
        
        result = await db.execute(
            select(Category).where(Category.is_active == True).order_by(Category.sort_order)
        )
        categories = result.scalars().all()
        
        data = [
            {
                "id": c.id,
                "name": c.name,
                "icon": c.icon,
                "sort_order": c.sort_order
            }
            for c in categories
        ]
        
        await CacheService.set_categories(data)
    
    @staticmethod
    async def warm_home_data(db) -> None:
        """预热首页数据"""
        from app.models.banner import Banner
        from app.models.announcement import Announcement
        from sqlalchemy import select
        
        # 预热轮播图
        result = await db.execute(
            select(Banner).where(Banner.is_active == True).order_by(Banner.sort_order)
        )
        banners = result.scalars().all()
        banner_data = [
            {
                "id": b.id,
                "image_url": b.image_url,
                "link_url": b.link_url,
                "title": b.title
            }
            for b in banners
        ]
        await CacheService.set_home_banners(banner_data)
        
        # 预热公告
        result = await db.execute(
            select(Announcement).where(Announcement.is_active == True).order_by(Announcement.created_at.desc()).limit(10)
        )
        announcements = result.scalars().all()
        announcement_data = [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in announcements
        ]
        await CacheService.set_home_announcements(announcement_data)
