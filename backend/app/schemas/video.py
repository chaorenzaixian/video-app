"""
视频相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.video import VideoStatus, VideoQuality


# 视频上传
class VideoUpload(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = []
    is_vip_only: bool = False


# 视频更新
class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    is_vip_only: Optional[bool] = None
    is_featured: Optional[bool] = None


# 视频响应
class VideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    preview_url: Optional[str] = None  # 预览视频URL（悬停播放）
    hls_url: Optional[str] = None
    duration: float
    status: VideoStatus
    quality: VideoQuality
    is_vip_only: bool
    is_featured: bool
    view_count: int
    like_count: int
    comment_count: int
    ai_summary: Optional[str] = None
    category_name: Optional[str] = None
    uploader_id: Optional[int] = None
    uploader_name: str
    uploader_avatar: Optional[str] = None
    uploader_vip_level: int = 0  # 上传者VIP等级
    created_at: datetime
    published_at: Optional[datetime] = None
    tags: List[str] = []
    needs_vip: bool = False  # 用户是否需要VIP才能观看
    
    # 付费/试看相关字段
    pay_type: Optional[str] = "free"  # free/coins/vip_free/vip_extra
    coin_price: int = 0               # 金币价格
    free_preview_seconds: int = 30    # 免费试看秒数
    is_purchased: bool = False        # 用户是否已购买
    
    class Config:
        from_attributes = True


# 视频列表
class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    page: int
    page_size: int


# 分类
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    video_count: int = 0
    parent_id: Optional[int] = None
    level: int = 1
    is_featured: bool = False
    category_type: str = "video"  # video/short/both
    sort_order: int = 0
    children: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True


# 解决循环引用
CategoryResponse.model_rebuild()


# 视频处理状态
class VideoProcessStatus(BaseModel):
    video_id: int
    status: VideoStatus
    progress: float = 0  # 处理进度 0-100
    message: Optional[str] = None




