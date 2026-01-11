"""
暗网视频专区模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Float, Table, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.video import VideoStatus, VideoQuality


# 暗网视频-标签关联表
darkweb_video_tags = Table(
    'darkweb_video_tags_association',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('darkweb_videos.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('darkweb_tags.id'), primary_key=True)
)


class DarkwebCategory(Base):
    """暗网视频分类表"""
    __tablename__ = "darkweb_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # 层级关系
    parent_id = Column(Integer, ForeignKey("darkweb_categories.id"), nullable=True)
    level = Column(Integer, default=1)  # 1=一级分类, 2=二级分类
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    videos = relationship("DarkwebVideo", back_populates="category")
    parent = relationship("DarkwebCategory", remote_side=[id], backref="children")


class DarkwebTag(Base):
    """暗网视频标签表"""
    __tablename__ = "darkweb_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)
    use_count = Column(Integer, default=0)
    
    # 关系
    videos = relationship("DarkwebVideo", secondary=darkweb_video_tags, back_populates="tags")


class DarkwebVideo(Base):
    """暗网视频表"""
    __tablename__ = "darkweb_videos"
    __table_args__ = (
        Index('idx_darkweb_status_created', 'status', 'created_at'),
        Index('idx_darkweb_category_status', 'category_id', 'status'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    
    # 视频文件
    original_url = Column(String(500), nullable=True)
    hls_url = Column(String(500), nullable=True)
    preview_url = Column(String(500), nullable=True)
    duration = Column(Float, default=0)
    file_size = Column(Integer, default=0)
    
    # 状态
    status = Column(Enum(VideoStatus), default=VideoStatus.UPLOADING)
    quality = Column(Enum(VideoQuality), default=VideoQuality.HD)
    is_featured = Column(Boolean, default=False)
    
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # 分类
    category_id = Column(Integer, ForeignKey("darkweb_categories.id"), nullable=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # 关系
    category = relationship("DarkwebCategory", back_populates="videos")
    uploader = relationship("User", backref="darkweb_videos")
    tags = relationship("DarkwebTag", secondary=darkweb_video_tags, back_populates="videos")


class DarkwebView(Base):
    """暗网视频观看记录表"""
    __tablename__ = "darkweb_views"
    __table_args__ = (
        Index('idx_darkweb_view_video', 'video_id', 'created_at'),
        Index('idx_darkweb_view_user', 'user_id', 'created_at'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("darkweb_videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    ip_address = Column(String(50), nullable=True)
    watch_duration = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
