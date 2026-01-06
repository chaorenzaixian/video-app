"""
举报系统模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Report(Base):
    """举报记录"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # 举报人
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 举报对象类型
    target_type = Column(String(50), nullable=False)  # video, comment, user, message
    target_id = Column(Integer, nullable=False)
    
    # 举报原因
    reason_type = Column(String(50), nullable=False)  # spam, porn, violence, fraud, other
    reason_detail = Column(Text, nullable=True)
    
    # 证据截图
    screenshots = Column(JSON, nullable=True)  # 截图URL列表
    
    # 处理状态
    status = Column(String(20), default="pending")  # pending, processing, resolved, rejected
    
    # 处理信息
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    handled_at = Column(DateTime, nullable=True)
    handle_result = Column(String(50), nullable=True)  # warn, delete, ban, dismiss
    handle_note = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportCategory(Base):
    """举报分类"""
    __tablename__ = "report_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    target_types = Column(JSON, nullable=True)  # 适用的举报对象类型
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

