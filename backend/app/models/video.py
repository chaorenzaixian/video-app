"""
视频相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Float, Table, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class VideoStatus(str, enum.Enum):
    """视频状态"""
    UPLOADING = "UPLOADING"     # 上传中
    PROCESSING = "PROCESSING"   # 处理中（转码）
    PUBLISHED = "PUBLISHED"     # 已发布
    FAILED = "FAILED"           # 处理失败
    DELETED = "DELETED"         # 已删除
    REVIEWING = "REVIEWING"     # 审核中


class VideoQuality(str, enum.Enum):
    """视频质量"""
    SD = "480p"
    HD = "720p"
    FHD = "1080p"
    QHD = "1440p"
    UHD = "2160p"


# 视频-标签关联表
video_tags = Table(
    'video_tags_association',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('video_tag.id'), primary_key=True)
)


class VideoCategory(Base):
    """视频分类表"""
    __tablename__ = "video_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)  # 是否推荐分类
    
    # 分类类型: video=普通视频, short=短视频, both=两者都适用
    category_type = Column(String(20), default="video")
    
    # 层级关系
    parent_id = Column(Integer, ForeignKey("video_categories.id"), nullable=True)
    level = Column(Integer, default=1)  # 1=一级分类, 2=二级分类
    
    # 关系
    videos = relationship("Video", back_populates="category")
    parent = relationship("VideoCategory", remote_side=[id], backref="children")


class ShortVideoCategory(Base):
    """短视频分类表（独立）"""
    __tablename__ = "short_video_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoTag(Base):
    """视频标签表"""
    __tablename__ = "video_tag"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    use_count = Column(Integer, default=0)
    
    # 关系
    videos = relationship("Video", secondary=video_tags, back_populates="tags")


class Video(Base):
    """视频表"""
    __tablename__ = "videos"
    __table_args__ = (
        # 复合索引：优化视频列表查询
        Index('idx_video_status_created', 'status', 'created_at'),
        Index('idx_video_category_status', 'category_id', 'status'),
        Index('idx_video_uploader_status', 'uploader_id', 'status'),
        Index('idx_video_featured_created', 'is_featured', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)  # 封面图
    
    # 视频文件
    original_url = Column(String(500), nullable=True)  # 原始视频URL
    hls_url = Column(String(500), nullable=True)       # HLS流地址
    preview_url = Column(String(500), nullable=True)   # 预览视频URL（悬停播放）
    duration = Column(Float, default=0)                # 时长（秒）
    file_size = Column(Integer, default=0)             # 文件大小（字节）
    
    # AI生成内容
    ai_summary = Column(Text, nullable=True)           # AI生成的摘要
    ai_tags = Column(String(500), nullable=True)       # AI识别的标签
    
    # 状态
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING)
    quality = Column(Enum(VideoQuality), default=VideoQuality.HD)
    is_vip_only = Column(Boolean, default=False)       # 是否VIP专享
    is_featured = Column(Boolean, default=False)       # 是否推荐
    is_short = Column(Boolean, default=False, index=True)  # 是否短视频（竖屏，≤10分钟）
    
    # 付费设置
    pay_type = Column(String(20), default="free")      # free/coins/vip_free/vip_extra
    coin_price = Column(Integer, default=0)            # 非会员金币价格
    vip_coin_price = Column(Integer, default=0)        # VIP会员金币价格（0表示VIP免费）
    vip_free_level = Column(Integer, default=0)        # 几级VIP免费(0=不免费)
    vip_discount = Column(Float, default=1.0)          # VIP折扣率（已弃用，改用vip_coin_price）
    free_preview_seconds = Column(Integer, default=15) # 免费试看秒数，默认15秒
    
    # 创作者相关
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=True)  # 创作者ID
    revenue_share_ratio = Column(Float, default=0.7)   # 创作者分成比例
    
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # 分类
    category_id = Column(Integer, ForeignKey("video_categories.id"), nullable=True)
    short_category_id = Column(Integer, ForeignKey("short_video_categories.id"), nullable=True)  # 短视频专用分类
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # 关系
    category = relationship("VideoCategory", back_populates="videos")
    short_category = relationship("ShortVideoCategory", backref="videos")  # 短视频分类关系
    uploader = relationship("User", back_populates="videos")
    tags = relationship("VideoTag", secondary=video_tags, back_populates="videos")
    comments = relationship("Comment", back_populates="video")
    views = relationship("VideoView", back_populates="video")


class VideoView(Base):
    """视频观看记录表"""
    __tablename__ = "video_views"
    __table_args__ = (
        # 复合索引：优化观看记录查询
        Index('idx_view_video_created', 'video_id', 'created_at'),  # 视频观看统计
        Index('idx_view_user_video', 'user_id', 'video_id'),        # 判断用户是否看过
        Index('idx_view_user_created', 'user_id', 'created_at'),    # 用户观看历史
    )
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # 可以为空（未登录用户）
    
    # 观看信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    watch_duration = Column(Float, default=0)  # 观看时长
    watch_progress = Column(Float, default=0)  # 观看进度（百分比）
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="views")

