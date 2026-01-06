"""
用户相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class VIPType(str, enum.Enum):
    """VIP类型"""
    MONTHLY = "monthly"       # 包月
    QUARTERLY = "quarterly"   # 包季度
    YEARLY = "yearly"         # 包年
    LIFETIME = "lifetime"     # 永久


class VIPLevel(int, enum.Enum):
    """VIP等级"""
    NONE = 0           # 非VIP
    VIP = 1            # 普通VIP
    VIP1 = 2           # VIP1
    VIP2 = 3           # VIP2
    VIP3 = 4           # VIP3
    GOLD = 5           # 黄金至尊
    SUPER_PURPLE = 6   # 紫色限定至尊


class UserRole(str, enum.Enum):
    """用户角色"""
    USER = "user"
    VIP = "vip"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)  # 游客可为空
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 设备信息（用于游客账号）
    device_id = Column(String(100), unique=True, index=True, nullable=True)
    is_guest = Column(Boolean, default=False)  # 是否游客账号
    
    # 用户信息
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    gender = Column(String(10), nullable=True)  # male, female, secret
    
    # 角色与状态
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 邀请系统
    invite_code = Column(String(20), unique=True, index=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invite_count = Column(Integer, default=0)  # 邀请人数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # 登录信息
    register_ip = Column(String(50), nullable=True)  # 注册IP
    last_login_ip = Column(String(50), nullable=True)  # 最近登录IP
    
    # 单设备登录控制
    current_session_id = Column(String(64), nullable=True, index=True)  # 当前有效会话ID
    current_device_info = Column(String(500), nullable=True)  # 当前设备信息
    
    # 关系
    vip = relationship("UserVIP", back_populates="user", uselist=False)
    videos = relationship("Video", back_populates="uploader")
    comments = relationship("Comment", back_populates="user")
    inviter = relationship("User", remote_side=[id], backref="invited_users")


class UserVIP(Base):
    """用户VIP信息表"""
    __tablename__ = "user_vips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # VIP状态
    vip_type = Column(Enum(VIPType), nullable=True)
    vip_level = Column(Integer, default=0)  # VIP等级: 0=非VIP, 1=普通VIP, 2=VIP1, 3=VIP2, 4=VIP3, 5=黄金至尊, 6=蓝色至尊, 7=紫色限定至尊
    is_active = Column(Boolean, default=False)
    
    # VIP时间
    start_date = Column(DateTime, nullable=True)
    expire_date = Column(DateTime, nullable=True)
    
    # 统计
    total_days = Column(Integer, default=0)  # 累计VIP天数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="vip")


class LoginQRToken(Base):
    """二维码登录令牌表"""
    __tablename__ = "login_qr_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 令牌信息
    token = Column(String(64), unique=True, index=True, nullable=False)  # 唯一登录令牌
    
    # 状态
    is_used = Column(Boolean, default=False)  # 是否已使用
    used_at = Column(DateTime, nullable=True)  # 使用时间
    used_device_info = Column(String(500), nullable=True)  # 使用设备信息
    used_ip = Column(String(50), nullable=True)  # 使用IP
    
    # 时间（永久有效，但只能用一次）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")


class TrustedDevice(Base):
    """可信设备表"""
    __tablename__ = "trusted_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 设备信息
    device_id = Column(String(64), nullable=False)  # 设备唯一标识（指纹）
    device_name = Column(String(100), nullable=True)  # 设备名称（如 iPhone, Windows PC）
    device_info = Column(String(500), nullable=True)  # 详细设备信息
    
    # 状态
    is_active = Column(Boolean, default=True)  # 是否激活
    last_login_at = Column(DateTime, nullable=True)  # 最后登录时间
    last_login_ip = Column(String(50), nullable=True)  # 最后登录IP
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")


class DeviceSwitchLog(Base):
    """设备切换记录表"""
    __tablename__ = "device_switch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 切换信息
    from_device_id = Column(String(64), nullable=True)  # 原设备
    to_device_id = Column(String(64), nullable=False)  # 新设备
    to_device_name = Column(String(100), nullable=True)
    to_device_ip = Column(String(50), nullable=True)
    
    # 时间
    switched_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User")