"""
支付相关Schema
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.payment import PaymentStatus, PaymentMethod, OrderType


# 创建订单
class CreateOrder(BaseModel):
    order_type: OrderType
    payment_method: PaymentMethod


# 订单响应
class OrderResponse(BaseModel):
    id: int
    order_no: str
    order_type: OrderType
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: Optional[PaymentMethod] = None
    pay_url: Optional[str] = None  # 支付链接
    created_at: datetime
    expire_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 支付回调
class PaymentCallback(BaseModel):
    order_no: str
    trade_no: str
    status: str
    amount: Decimal
    raw_data: Optional[str] = None


# 订单列表
class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int


# VIP价格
class VIPPriceResponse(BaseModel):
    monthly: Decimal
    quarterly: Decimal
    yearly: Decimal
    lifetime: Decimal
    currency: str = "CNY"









