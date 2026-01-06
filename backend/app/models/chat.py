"""
客服聊天相关模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ChatSessionStatus(str, enum.Enum):
    """会话状态"""
    WAITING = "waiting"      # 等待客服接入
    ACTIVE = "active"        # 进行中
    CLOSED = "closed"        # 已结束


class MessageType(str, enum.Enum):
    """消息类型"""
    TEXT = "text"            # 文本消息
    IMAGE = "image"          # 图片
    SYSTEM = "system"        # 系统消息


class ChatSession(Base):
    """客服聊天会话"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 客服信息
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 会话状态
    status = Column(String(20), default=ChatSessionStatus.WAITING.value)
    
    # 会话标题（用户第一条消息）
    title = Column(String(200), nullable=True)
    
    # 未读消息数（客服端）
    unread_count = Column(Integer, default=0)
    
    # 用户未读消息数
    user_unread_count = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # 关系
    messages = relationship("ChatMessage", back_populates="session", lazy="dynamic")


class ChatMessage(Base):
    """聊天消息"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 会话
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # 发送者
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_from_user = Column(Boolean, default=True)  # True=用户发送, False=客服发送
    
    # 消息内容
    message_type = Column(String(20), default=MessageType.TEXT.value)
    content = Column(Text, nullable=False)
    
    # 已读状态
    is_read = Column(Boolean, default=False)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    session = relationship("ChatSession", back_populates="messages")


class QuickReply(Base):
    """客服快捷回复"""
    __tablename__ = "quick_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 分类
    category = Column(String(50), nullable=True)
    
    # 内容
    title = Column(String(100), nullable=False)  # 标题/关键词
    content = Column(Text, nullable=False)       # 回复内容
    
    # 排序和状态
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # 使用次数
    use_count = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
