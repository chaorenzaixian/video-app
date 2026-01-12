"""
用户相关Schema
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import VIPType, UserRole


# 用户注册
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = None
    invite_code: Optional[str] = None  # 邀请码


# 游客注册
class GuestRegister(BaseModel):
    device_id: str = Field(..., min_length=10, max_length=100)  # 设备指纹


# 游客登录（根据设备ID）
class GuestLogin(BaseModel):
    device_id: str = Field(..., min_length=10, max_length=100)


# 绑定手机号
class BindPhone(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    code: str = Field(..., min_length=4, max_length=6)  # 验证码


# 绑定邮箱
class BindEmail(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=6)  # 验证码


# 升级账号（游客转正式）
class UpgradeAccount(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


# 用户登录
class UserLogin(BaseModel):
    username: str  # 可以是用户名、邮箱或手机号
    password: str


# 用户更新
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None  # male, female, secret
    email: Optional[str] = None  # 邮箱绑定/更换


# 用户响应
class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None  # 游客账号可能为空
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None  # male, female, secret
    role: UserRole
    invite_code: Optional[str] = None
    invite_count: int = 0
    is_vip: bool = False
    is_guest: bool = False  # 历史遗留字段，新用户均为正式用户
    vip_level: int = 0  # VIP等级: 0=非VIP, 1=普通VIP, 2=VIP1, 3=VIP2, 4=VIP3, 5=黄金至尊, 6=蓝色至尊, 7=紫色限定至尊
    vip_level_name: Optional[str] = None  # VIP等级名称
    vip_expire_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Token
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# VIP相关
class VIPInfo(BaseModel):
    is_active: bool
    vip_type: Optional[VIPType] = None
    start_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    total_days: int = 0


class VIPPurchase(BaseModel):
    vip_type: VIPType
    payment_method: str  # alipay, wechat, stripe


# 邀请
class InviteInfo(BaseModel):
    invite_code: str
    invite_count: int
    total_reward_days: int



