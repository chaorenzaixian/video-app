"""
社区功能数据模型 - 动态、话题、圈子
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Post(Base):
    """动态/帖子表"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 内容
    content = Column(Text, nullable=False)
    images = Column(JSON, default=list)  # 图片URL列表，最多9张
    video_url = Column(String(500), nullable=True)  # 视频URL（短视频）
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)  # 关联视频
    
    # 话题
    topic_ids = Column(JSON, default=list)  # 关联话题ID列表
    
    # 统计
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # 状态
    is_top = Column(Boolean, default=False)  # 置顶
    is_hot = Column(Boolean, default=False)  # 热门
    is_recommended = Column(Boolean, default=False)  # 推荐
    status = Column(String(20), default="published")  # draft/published/hidden/deleted
    
    # 权限
    visibility = Column(String(20), default="public")  # public/followers/private
    allow_comment = Column(Boolean, default=True)
    
    # 位置
    location = Column(String(100), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", backref="posts")
    video = relationship("Video", backref="shared_posts")
    
    __table_args__ = (
        Index('idx_post_user_created', 'user_id', 'created_at'),
        Index('idx_post_status_created', 'status', 'created_at'),
    )


class PostComment(Base):
    """动态评论表"""
    __tablename__ = "post_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 内容
    content = Column(Text, nullable=False)
    images = Column(JSON, default=list)  # 评论图片
    
    # 回复
    parent_id = Column(Integer, ForeignKey("post_comments.id", ondelete="CASCADE"), nullable=True)
    reply_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 回复的用户
    
    # 统计
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # 状态
    is_top = Column(Boolean, default=False)
    status = Column(String(20), default="visible")  # visible/hidden/deleted
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    post = relationship("Post", backref="comments")
    user = relationship("User", foreign_keys=[user_id], backref="post_comments")
    reply_to_user = relationship("User", foreign_keys=[reply_to_user_id])
    parent = relationship("PostComment", remote_side=[id], backref="replies")


class PostLike(Base):
    """动态点赞表"""
    __tablename__ = "post_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", backref="likes")
    user = relationship("User", backref="post_likes")
    
    __table_args__ = (
        Index('idx_post_like_unique', 'post_id', 'user_id', unique=True),
    )


class PostCommentLike(Base):
    """动态评论点赞表"""
    __tablename__ = "post_comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("post_comments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_post_comment_like_unique', 'comment_id', 'user_id', unique=True),
    )


class Topic(Base):
    """话题表 - 支持两级分类"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)  # 父级ID，为空表示顶级分类
    name = Column(String(50), nullable=False, index=True)
    
    # 分类信息
    level = Column(Integer, default=1)  # 1=顶级分类, 2=二级话题
    icon = Column(String(500), nullable=True)  # 顶级分类图标
    cover = Column(String(500), nullable=True)  # 封面图
    description = Column(Text, nullable=True)
    
    # 统计
    post_count = Column(Integer, default=0)
    follow_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    children_count = Column(Integer, default=0)  # 子话题数量
    
    # 状态
    is_hot = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系 - 自关联
    parent = relationship("Topic", remote_side=[id], backref="children")


class TopicFollow(Base):
    """话题关注表"""
    __tablename__ = "topic_follows"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    topic = relationship("Topic", backref="followers")
    user = relationship("User", backref="followed_topics")
    
    __table_args__ = (
        Index('idx_topic_follow_unique', 'topic_id', 'user_id', unique=True),
    )



# ========== 图集模型 ==========

class GalleryCategory(Base):
    """图集分类"""
    __tablename__ = "gallery_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Gallery(Base):
    """图集"""
    __tablename__ = "galleries"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("gallery_categories.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    cover = Column(String(500), nullable=False)  # 封面图
    images = Column(JSON, default=list)  # 图片列表
    description = Column(Text, nullable=True)
    
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    
    # 更新信息
    chapter_count = Column(Integer, default=1)  # 话数
    status = Column(String(20), default="ongoing")  # ongoing/completed
    
    # 状态
    is_hot = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("GalleryCategory", backref="galleries")


# ========== 小说模型 ==========

class NovelCategory(Base):
    """小说分类"""
    __tablename__ = "novel_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    novel_type = Column(String(20), default="text")  # text/audio
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Novel(Base):
    """小说"""
    __tablename__ = "novels"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("novel_categories.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=True)
    cover = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # 类型
    novel_type = Column(String(20), default="text")  # text/audio
    
    # 统计
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # 章节信息
    chapter_count = Column(Integer, default=0)
    status = Column(String(20), default="ongoing")  # ongoing/completed
    
    # 状态
    is_hot = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("NovelCategory", backref="novels")


class NovelChapter(Base):
    """小说章节"""
    __tablename__ = "novel_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_num = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)  # 文字内容
    audio_url = Column(String(500), nullable=True)  # 音频URL
    
    is_free = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    novel = relationship("Novel", backref="chapters")
