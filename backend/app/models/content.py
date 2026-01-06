"""
内容管理模型 - Banner、公告等
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Banner(Base):
    """首页Banner"""
    __tablename__ = "banners"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, comment="标题")
    image_url = Column(String(500), nullable=False, comment="图片地址")
    link_url = Column(String(500), nullable=True, comment="跳转链接")
    link_type = Column(String(20), default='url', comment="链接类型: url/video/vip/none")
    position = Column(String(20), default='home', comment="显示位置: home/video/profile/vip")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Notice(Base):
    """系统公告"""
    __tablename__ = "notices"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    notice_type = Column(String(20), default='info', comment="类型: info/warning/success/error")
    is_popup = Column(Boolean, default=False, comment="是否弹窗显示")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NoticeRead(Base):
    """用户已读公告记录"""
    __tablename__ = "notice_reads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=False)
    read_at = Column(DateTime, server_default=func.now())



