"""
社交功能数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class PrivateMessage(Base):
    """私信表"""
    __tablename__ = "private_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(Text)
    message_type = Column(String(20), default="text")      # text/image/video
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")


class MessageConversation(Base):
    """私信会话表"""
    __tablename__ = "message_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    last_message_id = Column(Integer, ForeignKey("private_messages.id"))
    last_message_at = Column(DateTime)
    
    user1_unread = Column(Integer, default=0)
    user2_unread = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoDanmaku(Base):
    """视频弹幕表"""
    __tablename__ = "video_danmakus"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content = Column(String(100), nullable=False)
    time_offset = Column(Float, nullable=False)            # 视频时间点(秒)
    
    color = Column(String(10), default="#FFFFFF")
    position = Column(String(10), default="scroll")        # scroll/top/bottom
    font_size = Column(Integer, default=25)
    
    is_visible = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", backref="danmakus")
    user = relationship("User", backref="danmakus")


class Playlist(Base):
    """播放列表表"""
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cover_image = Column(String(255))
    
    is_public = Column(Boolean, default=False)
    video_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="playlists")


class PlaylistVideo(Base):
    """播放列表视频关联表"""
    __tablename__ = "playlist_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    sort_order = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    playlist = relationship("Playlist", backref="videos")
    video = relationship("Video", backref="in_playlists")


class UserNotification(Base):
    """用户通知表"""
    __tablename__ = "user_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    notification_type = Column(String(30))                 # follow/like/comment/tip/system
    title = Column(String(100))
    content = Column(Text)
    
    related_type = Column(String(30))                      # video/user/order
    related_id = Column(Integer)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="notifications")


class VideoLike(Base):
    """视频点赞表"""
    __tablename__ = "video_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", backref="likes")
    user = relationship("User", backref="video_likes")


class VideoFavorite(Base):
    """视频收藏表"""
    __tablename__ = "video_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", backref="favorites")
    user = relationship("User", backref="video_favorites")

