"""
VIP会员卡和特权模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class VipCard(Base):
    """VIP会员卡"""
    __tablename__ = "vip_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, default=1, comment="VIP等级")
    name = Column(String(50), nullable=False, comment="卡片名称")
    display_title = Column(String(100), comment="显示标题（支持换行）")
    description = Column(Text, comment="卡片描述")
    
    # 卡片外观
    background_image = Column(String(255), comment="背景图片URL")
    badge_text = Column(String(50), comment="角标文字")
    
    # 关联的特权ID列表（新字段，替代旧的benefit_line1-4）
    privilege_ids = Column(JSON, default=list, comment="关联的特权ID列表")
    
    # 价格
    price = Column(Float, nullable=False, comment="售价")
    original_price = Column(Float, comment="原价")
    duration_days = Column(Integer, default=30, comment="有效天数，0表示永久")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VipPrivilege(Base):
    """VIP特权"""
    __tablename__ = "vip_privileges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="特权名称")
    description = Column(String(200), comment="特权描述")
    icon = Column(String(255), comment="图标URL")
    
    # 等级要求
    min_level = Column(Integer, default=1, comment="最低VIP等级要求")
    
    # 特权值（用于程序逻辑）
    privilege_key = Column(String(50), comment="特权标识键")
    privilege_value = Column(String(100), comment="特权值")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VipPurchaseRecord(Base):
    """VIP购买记录"""
    __tablename__ = "vip_purchase_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    card_id = Column(Integer, ForeignKey("vip_cards.id"), nullable=False)
    card_name = Column(String(50), comment="购买时的卡片名称")
    
    amount = Column(Float, nullable=False, comment="支付金额")
    duration_days = Column(Integer, comment="购买的天数")
    
    order_no = Column(String(64), unique=True, index=True, comment="订单号")
    payment_method = Column(String(20), comment="支付方式")
    status = Column(String(20), default="pending", comment="状态: pending/paid/cancelled")
    
    paid_at = Column(DateTime, comment="支付时间")
    created_at = Column(DateTime, server_default=func.now())



















