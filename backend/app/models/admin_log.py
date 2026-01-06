"""
管理员操作日志模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class AdminLog(Base):
    """管理员操作日志"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 操作人
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    admin_username = Column(String(100), nullable=False)
    
    # 操作类型
    action = Column(String(50), nullable=False)  # create/update/delete/ban/approve/reject等
    module = Column(String(50), nullable=False)  # user/video/comment/order/agent等
    
    # 操作对象
    target_type = Column(String(50), nullable=True)  # 对象类型
    target_id = Column(Integer, nullable=True)       # 对象ID
    target_name = Column(String(255), nullable=True) # 对象名称（便于展示）
    
    # 操作详情
    description = Column(Text, nullable=True)        # 操作描述
    before_data = Column(JSON, nullable=True)        # 修改前数据
    after_data = Column(JSON, nullable=True)         # 修改后数据
    
    # 请求信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 关系
    admin = relationship("User", foreign_keys=[admin_id])












