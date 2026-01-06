"""
支付相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    """支付状态"""
    PENDING = "pending"       # 待支付
    PROCESSING = "processing" # 处理中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    REFUNDED = "refunded"     # 已退款
    CANCELLED = "cancelled"   # 已取消


class PaymentMethod(str, enum.Enum):
    """支付方式"""
    ALIPAY = "alipay"         # 支付宝
    WECHAT = "wechat"         # 微信支付
    STRIPE = "stripe"         # Stripe（国际支付）
    APPLE = "apple"           # Apple Pay
    GOOGLE = "google"         # Google Pay


class OrderType(str, enum.Enum):
    """订单类型"""
    VIP_MONTHLY = "vip_monthly"
    VIP_QUARTERLY = "vip_quarterly"
    VIP_YEARLY = "vip_yearly"
    VIP_LIFETIME = "vip_lifetime"


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__ = "payment_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(64), unique=True, index=True, nullable=False)  # 订单号
    
    # 用户
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 订单信息
    order_type = Column(Enum(OrderType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # 金额（元）
    currency = Column(String(10), default="CNY")     # 货币
    
    # 支付信息
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # 第三方支付信息
    trade_no = Column(String(128), nullable=True)  # 第三方交易号
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    expire_at = Column(DateTime, nullable=True)  # 订单过期时间
    
    # 关系
    user = relationship("User")
    payment = relationship("Payment", back_populates="order", uselist=False)


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联订单
    order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=False)
    
    # 支付详情
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # 第三方回调信息
    trade_no = Column(String(128), nullable=True)
    callback_data = Column(String(2000), nullable=True)  # 回调原始数据
    
    # 状态
    status = Column(Enum(PaymentStatus), default=PaymentStatus.SUCCESS)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    order = relationship("PaymentOrder", back_populates="payment")









