"""
评论相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Comment(Base):
    """评论表"""
    __tablename__ = "comments"
    __table_args__ = (
        # 复合索引：优化评论列表查询
        Index('idx_comment_video_created', 'video_id', 'created_at'),
        Index('idx_comment_video_hidden', 'video_id', 'is_hidden'),
        Index('idx_comment_user_created', 'user_id', 'created_at'),
        Index('idx_comment_parent_id', 'parent_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 内容
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)  # 评论图片
    
    # 关联
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # 回复的评论ID
    
    # 统计
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # 状态
    is_pinned = Column(Boolean, default=False)   # 是否置顶
    is_hidden = Column(Boolean, default=False)   # 是否隐藏
    is_official = Column(Boolean, default=False)  # 是否官方评论
    is_god = Column(Boolean, default=False)      # 是否神评
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    video = relationship("Video", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", backref="comment", lazy="dynamic")


class CommentLike(Base):
    """评论点赞表"""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)






