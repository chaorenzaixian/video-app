"""
广告相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AdPosition(str, enum.Enum):
    """广告位置"""
    SPLASH = "SPLASH"                 # 开屏广告
    HOME_BANNER = "HOME_BANNER"       # 首页横幅
    HOME_POPUP = "HOME_POPUP"         # 首页弹窗
    VIDEO_PRE = "VIDEO_PRE"           # 视频前贴
    VIDEO_MID = "VIDEO_MID"           # 视频中插
    VIDEO_POST = "VIDEO_POST"         # 视频后贴
    SIDEBAR = "SIDEBAR"               # 侧边栏
    FEED = "FEED"                     # 信息流


class AdType(str, enum.Enum):
    """广告类型"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    HTML = "HTML"


class Advertisement(Base):
    """广告表"""
    __tablename__ = "advertisements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # 广告内容
    ad_type = Column(Enum(AdType), default=AdType.IMAGE)
    media_url = Column(String(500), nullable=True)   # 图片/视频URL
    html_content = Column(Text, nullable=True)       # HTML内容
    target_url = Column(String(500), nullable=True)  # 跳转链接
    
    # 展示设置
    position = Column(Enum(AdPosition), nullable=False)
    priority = Column(Integer, default=0)            # 优先级
    duration = Column(Integer, default=5)            # 展示时长（秒）
    
    # 定向设置
    target_vip = Column(Boolean, default=False)      # 是否仅对VIP展示（通常VIP不展示广告）
    
    # 统计
    impression_count = Column(Integer, default=0)    # 展示次数
    click_count = Column(Integer, default=0)         # 点击次数
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 时间
    start_date = Column(DateTime, nullable=True)     # 开始时间
    end_date = Column(DateTime, nullable=True)       # 结束时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    clicks = relationship("AdClick", back_populates="ad")


class AdClick(Base):
    """广告点击记录表"""
    __tablename__ = "ad_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("advertisements.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 点击信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    ad = relationship("Advertisement", back_populates="clicks")


class IconAd(Base):
    """图标广告位（首页固定10个位置）"""
    __tablename__ = "icon_ads"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(50), nullable=False)          # 显示名称
    icon = Column(String(50), nullable=True)           # emoji图标
    image = Column(String(500), nullable=True)         # 图片URL（优先于icon）
    bg = Column(String(200), nullable=False)           # 背景渐变色
    badge = Column(String(50), nullable=True)          # 角标文字
    badge_type = Column(String(20), nullable=True)     # 角标样式: hot/purple/gold/blue/pink/cyan/red/orange
    link = Column(String(500), nullable=True)          # 跳转链接
    
    # 排序和状态
    sort_order = Column(Integer, default=0)            # 排序（1-10）
    is_active = Column(Boolean, default=True)          # 是否启用
    
    # 统计
    click_count = Column(Integer, default=0)           # 点击次数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FuncEntry(Base):
    """功能入口图标（首页功能区）"""
    __tablename__ = "func_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(50), nullable=False)          # 显示名称
    image = Column(String(500), nullable=True)         # 图标图片URL
    link = Column(String(500), nullable=True)          # 跳转链接
    
    # 排序和状态
    sort_order = Column(Integer, default=0)            # 排序
    is_active = Column(Boolean, default=True)          # 是否启用
    
    # 统计
    click_count = Column(Integer, default=0)           # 点击次数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Announcement(Base):
    """公告表"""
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 公告内容
    content = Column(Text, nullable=False)             # 公告内容
    link = Column(String(500), nullable=True)          # 跳转链接
    
    # 排序和状态
    sort_order = Column(Integer, default=0)            # 排序（数字越大越靠前）
    is_active = Column(Boolean, default=True)          # 是否启用
    
    # 时间
    start_date = Column(DateTime, nullable=True)       # 开始时间
    end_date = Column(DateTime, nullable=True)         # 结束时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OfficialGroupType(str, enum.Enum):
    """官方群组类型"""
    COMMUNITY = "community"      # 社区群
    BUSINESS = "business"        # 商务群


class OfficialGroup(Base):
    """官方群组表"""
    __tablename__ = "official_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)         # 群名称
    group_type = Column(Enum(OfficialGroupType), nullable=False)  # 群类型
    icon_type = Column(String(50), nullable=True)      # 图标类型: rocket/telegram/briefcase/heart等
    icon_bg = Column(String(200), nullable=True)       # 图标背景渐变
    url = Column(String(500), nullable=False)          # 群链接
    
    # 排序和状态
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerService(Base):
    """客服配置表"""
    __tablename__ = "customer_services"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(100), nullable=False)         # 客服名称
    service_type = Column(String(50), nullable=False, default="online")  # 类型: telegram/whatsapp/qq/wechat等
    contact = Column(String(500), nullable=False)      # 联系方式/链接
    icon_type = Column(String(50), default="headset")  # 图标类型
    icon_image = Column(String(500), nullable=True)    # 自定义图标URL
    icon_bg = Column(String(50), default="#667eea")    # 图标背景色
    description = Column(Text, nullable=True)          # 描述
    work_time = Column(String(100), nullable=True)     # 工作时间
    
    # 排序和状态
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)           # 点击次数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
