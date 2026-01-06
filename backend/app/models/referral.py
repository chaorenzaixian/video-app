"""
推广返利增强系统数据模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReferralLevel(Base):
    """多级分销配置"""
    __tablename__ = "referral_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)   # 层级 1-3
    commission_percent = Column(Float, nullable=False)     # 返利比例(%)
    min_recharge = Column(Numeric(10, 2), default=0)       # 最低充值金额才返利
    description = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RechargeCommission(Base):
    """充值返利记录"""
    __tablename__ = "recharge_commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联信息
    recharge_order_id = Column(Integer, nullable=False)    # 充值订单ID
    beneficiary_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 获益人(推广者)
    source_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 充值人
    
    # 返利信息
    referral_level = Column(Integer, nullable=False)       # 第几级推广
    recharge_amount = Column(Numeric(10, 2), nullable=False)  # 充值金额
    commission_percent = Column(Float, nullable=False)     # 返利比例
    commission_amount = Column(Numeric(10, 2), nullable=False)  # 返利金额
    
    # 状态
    status = Column(String(20), default="pending")         # pending/settled/cancelled
    settled_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    beneficiary = relationship("User", foreign_keys=[beneficiary_id])
    source_user = relationship("User", foreign_keys=[source_user_id])


class PromoLink(Base):
    """推广链接追踪"""
    __tablename__ = "promo_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    link_code = Column(String(20), unique=True, nullable=False)
    channel = Column(String(50))                           # 渠道标识
    description = Column(String(255))
    
    # 统计数据
    click_count = Column(Integer, default=0)
    register_count = Column(Integer, default=0)
    recharge_count = Column(Integer, default=0)
    total_recharge = Column(Numeric(10, 2), default=0)
    total_commission = Column(Numeric(10, 2), default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="promo_links")


class PromoClickLog(Base):
    """推广点击日志"""
    __tablename__ = "promo_click_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("promo_links.id"), nullable=False)
    
    ip_address = Column(String(50))
    user_agent = Column(Text)
    referer = Column(Text)
    
    # 转化信息
    registered_user_id = Column(Integer, ForeignKey("users.id"))
    converted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    link = relationship("PromoLink", backref="click_logs")


class ReferralChain(Base):
    """推广链条(用于多级分销)"""
    __tablename__ = "referral_chains"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # 上级链条 (JSON存储多级上级ID)
    # 例如: [直接上级ID, 二级上级ID, 三级上级ID]
    parent_chain = Column(JSON)
    
    # 直接上级
    direct_parent_id = Column(Integer, ForeignKey("users.id"))
    
    # 统计
    direct_invites = Column(Integer, default=0)            # 直接邀请人数
    total_team_size = Column(Integer, default=0)           # 团队总人数
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], backref="referral_chain")

