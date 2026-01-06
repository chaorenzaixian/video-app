"""
积分与任务系统模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserPoints(Base):
    """用户积分表"""
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_points = Column(Integer, default=0)        # 累计获得积分
    available_points = Column(Integer, default=0)    # 可用积分
    frozen_points = Column(Integer, default=0)       # 冻结积分
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="points")


class Task(Base):
    """任务配置表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), unique=True, nullable=False)  # checkin/post/comment/invite等
    task_name = Column(String(100), nullable=False)              # 任务名称
    task_desc = Column(String(255))                              # 任务描述
    points_reward = Column(Integer, default=0)                   # 积分奖励
    daily_limit = Column(Integer, default=1)                     # 每日可完成次数，0=无限
    icon = Column(String(255))                                   # 图标（emoji或图片路径）
    icon_bg = Column(String(50))                                 # 图标背景色
    action_type = Column(String(50), default="claim")            # claim=领取/redirect=跳转
    action_url = Column(String(255))                             # 跳转URL
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskRecord(Base):
    """任务完成记录表"""
    __tablename__ = "task_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    task_type = Column(String(50))                               # 冗余字段，方便查询
    completed_at = Column(DateTime, default=datetime.utcnow)
    points_earned = Column(Integer, default=0)
    status = Column(String(20), default="pending")               # pending/claimed/expired
    
    user = relationship("User")
    task = relationship("Task")


class PointLog(Base):
    """积分变动记录表"""
    __tablename__ = "point_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_amount = Column(Integer, nullable=False)              # 变动数量（正/负）
    change_type = Column(String(50))                             # task/exchange/admin/expire
    source_type = Column(String(50))                             # 来源类型
    source_id = Column(Integer)                                  # 来源ID
    balance_after = Column(Integer)                              # 变动后余额
    remark = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")


class ExchangeItem(Base):
    """兑换商品表"""
    __tablename__ = "exchange_items"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)              # 商品名称
    item_desc = Column(String(255))                              # 商品描述
    item_type = Column(String(50))                               # vip_days/coupon/gift
    item_value = Column(Integer)                                 # 商品价值（VIP天数/优惠券金额）
    points_cost = Column(Integer, nullable=False)                # 所需积分
    stock = Column(Integer, default=-1)                          # 库存（-1无限）
    daily_limit = Column(Integer, default=1)                     # 每日限兑次数
    icon = Column(String(255))
    image_url = Column(String(500))                              # 卡片背景图片
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExchangeRecord(Base):
    """兑换记录表"""
    __tablename__ = "exchange_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("exchange_items.id"), nullable=False)
    item_name = Column(String(100))                              # 冗余字段
    points_spent = Column(Integer)
    status = Column(String(20), default="success")               # success/pending/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    item = relationship("ExchangeItem")
