"""
交友模块模型 - 群聊、主播等
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from app.core.database import Base


class DatingGroup(Base):
    """交友群聊表"""
    __tablename__ = "dating_groups"
    __table_args__ = (
        Index('idx_dating_group_status', 'is_active', 'sort_order'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    avatar = Column(String(500), nullable=True)
    
    # 群聊链接
    join_url = Column(String(500), nullable=True)
    
    # 统计显示
    member_count = Column(String(20), default='0')  # 显示用，如 "10w"
    
    # 费用
    coin_cost = Column(Integer, default=0)
    is_free = Column(Boolean, default=False)
    
    # 状态
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # 分类: soul=SOUL群, chat=裸聊, live=直播
    category = Column(String(20), default='soul')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatingHost(Base):
    """交友主播表"""
    __tablename__ = "dating_hosts"
    __table_args__ = (
        Index('idx_dating_host_status', 'is_active', 'sort_order'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    nickname = Column(String(50), nullable=False)
    avatar = Column(String(500), nullable=True)
    
    # 详细信息
    age = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    weight = Column(Integer, nullable=True)
    cup = Column(String(5), nullable=True)
    
    # 统计显示
    chat_count = Column(Integer, default=0)
    
    # 标签
    is_vip = Column(Boolean, default=False)
    is_ace = Column(Boolean, default=False)  # 王牌主播
    
    # 跳转链接
    profile_url = Column(String(500), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # 分类: chat=裸聊, live=直播
    category = Column(String(20), default='chat')
    
    # 子分类: 学生萝莉, 人妻少妇, 主播御姐, 模特兼职 等
    sub_category = Column(String(30), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
