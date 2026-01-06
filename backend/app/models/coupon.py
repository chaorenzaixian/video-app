"""
优惠券系统数据模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class CouponTemplate(Base):
    """优惠券模板"""
    __tablename__ = "coupon_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 优惠类型
    coupon_type = Column(String(30), nullable=False)        # recharge/video/vip/universal
    discount_type = Column(String(20), nullable=False)      # percent/fixed/coins
    discount_value = Column(Numeric(10, 2), nullable=False) # 折扣值(百分比/固定金额/金币数)
    
    # 使用条件
    min_amount = Column(Numeric(10, 2), default=0)          # 最低消费金额
    max_discount = Column(Numeric(10, 2))                   # 最大优惠金额
    
    # 发放数量
    total_quantity = Column(Integer, default=-1)            # 总数量(-1无限)
    remaining_quantity = Column(Integer, default=-1)
    per_user_limit = Column(Integer, default=1)             # 每人限领次数
    
    # 有效期
    valid_days = Column(Integer)                            # 领取后有效天数
    start_time = Column(DateTime)                           # 活动开始时间
    end_time = Column(DateTime)                             # 活动结束时间
    
    # 适用范围
    applicable_items = Column(JSON)                         # 适用商品/视频ID列表
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCoupon(Base):
    """用户优惠券"""
    __tablename__ = "user_coupons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("coupon_templates.id"), nullable=False)
    
    coupon_code = Column(String(20), unique=True)           # 优惠券码
    
    status = Column(String(20), default="unused")           # unused/used/expired
    used_at = Column(DateTime)
    used_order_id = Column(Integer)                         # 使用的订单ID
    
    expire_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="coupons")
    template = relationship("CouponTemplate", backref="user_coupons")


class NewUserPackage(Base):
    """新用户礼包"""
    __tablename__ = "new_user_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 礼包内容
    contents = Column(JSON)                                 # {"coins": 100, "vip_days": 3, "coupons": [1,2]}
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NewUserPackageClaim(Base):
    """新用户礼包领取记录"""
    __tablename__ = "new_user_package_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    package_id = Column(Integer, ForeignKey("new_user_packages.id"), nullable=False)
    
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="package_claim")


class PromotionalEvent(Base):
    """促销活动"""
    __tablename__ = "promotional_events"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    event_type = Column(String(30), nullable=False)         # flash_sale/double_coins/discount
    
    # 活动配置
    config = Column(JSON)                                   # 活动具体配置
    
    # 活动时间
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

