"""
数据库查询优化工具
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Type, TypeVar, Any
from datetime import datetime

T = TypeVar('T')


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def paginate(query, page: int = 1, page_size: int = 20):
        """分页查询"""
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)
    
    @staticmethod
    async def count(db: AsyncSession, query) -> int:
        """高效计数"""
        count_query = select(func.count()).select_from(query.subquery())
        result = await db.execute(count_query)
        return result.scalar() or 0
    
    @staticmethod
    async def paginated_query(
        db: AsyncSession,
        query,
        page: int = 1,
        page_size: int = 20,
        count_total: bool = True
    ) -> tuple:
        """
        分页查询，返回 (items, total, has_more)
        """
        # 计算总数（可选）
        total = 0
        if count_total:
            total = await QueryOptimizer.count(db, query)
        
        # 分页
        offset = (page - 1) * page_size
        paginated = query.offset(offset).limit(page_size + 1)  # 多取一条判断是否有更多
        
        result = await db.execute(paginated)
        items = list(result.scalars().all())
        
        # 判断是否有更多
        has_more = len(items) > page_size
        if has_more:
            items = items[:page_size]
        
        return items, total, has_more


class VideoQueryBuilder:
    """视频查询构建器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._query = None
        self._filters = []
        self._order_by = None
        self._preload = []
    
    def base_query(self):
        """基础查询"""
        from app.models.video import Video, VideoStatus
        self._query = select(Video).where(Video.status == VideoStatus.PUBLISHED)
        return self
    
    def exclude_shorts(self):
        """排除短视频"""
        from app.models.video import Video
        self._filters.append(Video.is_short != True)
        return self
    
    def only_shorts(self):
        """只查短视频"""
        from app.models.video import Video
        self._filters.append(Video.is_short == True)
        return self
    
    def category(self, category_id: Optional[int]):
        """按分类筛选"""
        if category_id:
            from app.models.video import Video
            self._filters.append(Video.category_id == category_id)
        return self
    
    def search(self, keyword: Optional[str]):
        """搜索"""
        if keyword:
            from app.models.video import Video
            self._filters.append(Video.title.ilike(f"%{keyword}%"))
        return self
    
    def vip_only(self, is_vip: bool = True):
        """VIP视频筛选"""
        from app.models.video import Video
        self._filters.append(Video.is_vip_only == is_vip)
        return self
    
    def featured(self, is_featured: bool = True):
        """推荐视频筛选"""
        from app.models.video import Video
        self._filters.append(Video.is_featured == is_featured)
        return self
    
    def order_by_hot(self):
        """按热度排序"""
        from app.models.video import Video
        self._order_by = [Video.view_count.desc(), Video.created_at.desc()]
        return self
    
    def order_by_new(self):
        """按最新排序"""
        from app.models.video import Video
        self._order_by = [Video.created_at.desc()]
        return self
    
    def order_by_views(self):
        """按播放量排序"""
        from app.models.video import Video
        self._order_by = [Video.view_count.desc()]
        return self
    
    def preload_category(self):
        """预加载分类"""
        from app.models.video import Video
        self._preload.append(selectinload(Video.category))
        return self
    
    def preload_tags(self):
        """预加载标签"""
        from app.models.video import Video
        self._preload.append(selectinload(Video.tags))
        return self
    
    def preload_uploader(self):
        """预加载上传者"""
        from app.models.video import Video
        self._preload.append(selectinload(Video.uploader))
        return self
    
    def build(self):
        """构建查询"""
        query = self._query
        
        # 应用过滤条件
        for f in self._filters:
            query = query.where(f)
        
        # 应用排序
        if self._order_by:
            for order in self._order_by:
                query = query.order_by(order)
        
        # 应用预加载
        if self._preload:
            query = query.options(*self._preload)
        
        return query
    
    async def execute(self, page: int = 1, page_size: int = 20) -> tuple:
        """执行查询"""
        query = self.build()
        return await QueryOptimizer.paginated_query(
            self.db, query, page, page_size
        )


def format_video_response(video, include_tags: bool = False) -> dict:
    """格式化视频响应"""
    data = {
        "id": video.id,
        "title": video.title,
        "cover_url": video.cover_url,
        "preview_url": getattr(video, 'preview_url', None),
        "hls_url": video.hls_url,
        "duration": video.duration or 0,
        "view_count": video.view_count or 0,
        "like_count": video.like_count or 0,
        "comment_count": video.comment_count or 0,
        "is_vip_only": getattr(video, 'is_vip_only', False),
        "is_featured": getattr(video, 'is_featured', False),
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }
    
    # 分类信息
    if hasattr(video, 'category') and video.category:
        data["category_name"] = video.category.name
        data["category_id"] = video.category.id
    
    # 上传者信息
    if hasattr(video, 'uploader') and video.uploader:
        data["uploader_name"] = video.uploader.nickname or video.uploader.username
        data["uploader_avatar"] = video.uploader.avatar
    
    # 标签
    if include_tags and hasattr(video, 'tags'):
        data["tags"] = [tag.name for tag in video.tags] if video.tags else []
    
    return data
