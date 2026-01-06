"""
评论相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 评论创建
class CommentCreate(BaseModel):
    content: str = Field("", max_length=1000)  # 允许空内容（如果有图片）
    video_id: int
    parent_id: Optional[int] = None  # 回复的评论ID
    image_url: Optional[str] = None  # 评论图片


# 评论更新
class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


# 评论响应
class CommentResponse(BaseModel):
    id: int
    content: str
    image_url: Optional[str] = None  # 评论图片
    video_id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    user_vip_level: int = 0  # 用户VIP等级
    parent_id: Optional[int] = None
    like_count: int
    reply_count: int
    is_pinned: bool
    is_official: bool = False  # 是否官方评论
    is_liked: bool = False  # 当前用户是否点赞
    created_at: datetime
    replies: List["CommentResponse"] = []
    
    class Config:
        from_attributes = True


# 评论列表
class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int






