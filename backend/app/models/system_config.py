"""
系统配置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)  # 配置键
    value = Column(Text, nullable=True)  # 配置值
    description = Column(String(255), nullable=True)  # 配置描述
    group_name = Column(String(50), default="general")  # 配置分组
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 默认配置项
DEFAULT_CONFIGS = [
    # 账号凭证页配置
    {"key": "credential_site_name", "value": "Soul成人版", "description": "账号凭证-网站名称", "group_name": "credential"},
    {"key": "credential_site_url", "value": "https://soul9.fm", "description": "账号凭证-官网地址", "group_name": "credential"},
    {"key": "credential_tip", "value": "提示*扫码可直接登录，仅限一台设备使用", "description": "账号凭证-提示文字", "group_name": "credential"},
    
    # 基础配置
    {"key": "site_name", "value": "视频平台", "description": "网站名称", "group_name": "basic"},
    {"key": "site_logo", "value": "", "description": "网站Logo", "group_name": "basic"},
    {"key": "contact_email", "value": "", "description": "联系邮箱", "group_name": "basic"},
    {"key": "contact_telegram", "value": "", "description": "Telegram群组", "group_name": "basic"},
    
    # 分享配置
    {"key": "share_title", "value": "邀请好友，赚取VIP", "description": "分享标题", "group_name": "share"},
    {"key": "share_desc", "value": "注册即送VIP，快来加入", "description": "分享描述", "group_name": "share"},
]

