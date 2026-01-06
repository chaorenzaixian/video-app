"""
金币系统数据模型
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, JSON, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserCoins(Base):
    """用户金币账户"""
    __tablename__ = "user_coins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)                    # 金币余额
    total_recharged = Column(Integer, default=0)            # 累计充值金币
    total_spent = Column(Integer, default=0)                # 累计消费金币
    total_earned = Column(Integer, default=0)               # 累计赚取金币(创作者收益等)
    frozen = Column(Integer, default=0)                     # 冻结金币
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="coins_account")


class CoinTransaction(Base):
    """金币交易记录"""
    __tablename__ = "coin_transactions"
    __table_args__ = (
        # 复合索引：优化用户交易记录查询
        Index('idx_coin_tx_user_created', 'user_id', 'created_at'),
        Index('idx_coin_tx_user_type', 'user_id', 'transaction_type'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)                # 变动数量(正数增加,负数减少)
    balance_after = Column(Integer, nullable=False)         # 变动后余额
    
    transaction_type = Column(String(30), nullable=False)   # recharge/purchase/tip/earn/refund/withdraw/admin
    source_type = Column(String(30))                        # video/collection/gift/system/creator
    source_id = Column(Integer)                             # 关联ID
    
    description = Column(String(255))                       # 描述
    extra_data = Column(JSON)                               # 额外数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="coin_transactions")


class RechargePackage(Base):
    """充值套餐"""
    __tablename__ = "recharge_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)              # 套餐名称
    coins = Column(Integer, nullable=False)                 # 金币数量
    bonus_coins = Column(Integer, default=0)                # 赠送金币
    price = Column(Numeric(10, 2), nullable=False)          # 价格(元)
    original_price = Column(Numeric(10, 2))                 # 原价
    
    icon = Column(String(255))                              # 图标
    tag = Column(String(50))                                # 标签(热门/推荐/限时)
    description = Column(String(255))                       # 描述
    
    is_hot = Column(Boolean, default=False)                 # 热门推荐
    is_first_charge = Column(Boolean, default=False)        # 首充专享
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RechargeOrder(Base):
    """充值订单"""
    __tablename__ = "recharge_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)  # 订单号
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("recharge_packages.id"))
    
    coins = Column(Integer, nullable=False)                 # 购买金币数
    bonus_coins = Column(Integer, default=0)                # 赠送金币
    amount = Column(Numeric(10, 2), nullable=False)         # 支付金额
    
    payment_method = Column(String(30))                     # alipay/wechat/card
    payment_no = Column(String(100))                        # 第三方支付单号
    
    status = Column(String(20), default="pending")          # pending/paid/failed/refunded
    paid_at = Column(DateTime)
    
    # 推广返利相关
    inviter_id = Column(Integer, ForeignKey("users.id"))    # 邀请人ID
    commission_processed = Column(Boolean, default=False)   # 返利是否已处理
    
    ip_address = Column(String(50))
    user_agent = Column(Text)
    extra_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], backref="recharge_orders")
    package = relationship("RechargePackage", backref="orders")


class VideoPurchase(Base):
    """视频购买记录"""
    __tablename__ = "video_purchases"
    __table_args__ = (
        # 复合索引：优化购买记录查询
        Index('idx_purchase_user_video', 'user_id', 'video_id'),    # 判断用户是否购买过（高频查询）
        Index('idx_purchase_video_created', 'video_id', 'created_at'),  # 视频购买统计
        Index('idx_purchase_user_created', 'user_id', 'created_at'),    # 用户购买历史
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    
    coins_paid = Column(Integer, nullable=False)            # 支付金币
    original_price = Column(Integer)                        # 原价
    discount_info = Column(String(100))                     # 折扣信息(VIP折扣等)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="video_purchases")
    video = relationship("Video", backref="purchases")


class CollectionPurchase(Base):
    """合集购买记录"""
    __tablename__ = "collection_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_id = Column(Integer, nullable=False)         # 合集ID
    
    purchase_type = Column(String(20), default="full")      # full/single
    episodes_purchased = Column(JSON)                       # 购买的集数(单集购买)
    coins_paid = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="collection_purchases")
