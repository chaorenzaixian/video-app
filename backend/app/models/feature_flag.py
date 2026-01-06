"""
功能开关/AB测试/灰度发布 模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class FeatureFlag(Base):
    """功能开关/实验配置表"""
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # 功能标识
    name = Column(String(200), nullable=False)  # 功能名称
    description = Column(Text, nullable=True)  # 描述
    
    # 类型
    flag_type = Column(String(20), default="boolean")
    # boolean: 开/关
    # percentage: 百分比灰度
    # ab_test: AB测试
    # whitelist: 白名单
    # rule: 规则匹配
    
    # 状态
    is_enabled = Column(Boolean, default=False)  # 总开关
    
    # 默认值（JSON格式）
    default_value = Column(Text, default='{"enabled": false}')
    
    # 变体配置（AB测试用，JSON格式）
    # 示例: [{"name": "control", "value": {...}, "weight": 50}, {"name": "treatment", "value": {...}, "weight": 50}]
    variants = Column(Text, nullable=True)
    
    # 灰度百分比 (0-100)
    rollout_percentage = Column(Integer, default=0)
    
    # 白名单用户ID（JSON数组）
    whitelist_user_ids = Column(Text, nullable=True)  # 示例: [1, 2, 3]
    
    # 时间控制
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # 统计
    exposure_count = Column(Integer, default=0)  # 曝光次数
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    rules = relationship("FeatureRule", back_populates="flag", cascade="all, delete-orphan")


class FeatureRule(Base):
    """功能规则表（细粒度控制）"""
    __tablename__ = "feature_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("feature_flags.id", ondelete="CASCADE"), nullable=False)
    
    # 规则名称
    name = Column(String(100), nullable=False)
    
    # 匹配条件（JSON格式）
    # 示例: {"user_id": {"in": [1,2,3]}, "vip_level": {"gte": 3}, "device": {"eq": "ios"}}
    conditions = Column(Text, nullable=False)
    
    # 匹配后返回的值（JSON格式）
    value = Column(Text, nullable=False)
    
    # 优先级（数字越小优先级越高）
    priority = Column(Integer, default=100)
    
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    flag = relationship("FeatureFlag", back_populates="rules")


class ExperimentExposure(Base):
    """实验曝光记录表（用于数据分析）"""
    __tablename__ = "experiment_exposures"
    
    id = Column(Integer, primary_key=True, index=True)
    flag_key = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    variant_name = Column(String(50), nullable=False)  # 分配到的变体
    
    # 上下文信息
    device_type = Column(String(20), nullable=True)
    app_version = Column(String(20), nullable=True)
    
    # 时间
    exposed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_exposure_flag_user', 'flag_key', 'user_id'),
    )


class ExperimentEvent(Base):
    """实验事件表（用于转化分析）"""
    __tablename__ = "experiment_events"
    
    id = Column(Integer, primary_key=True, index=True)
    flag_key = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    variant_name = Column(String(50), nullable=False)
    
    # 事件信息
    event_type = Column(String(50), nullable=False)  # click, purchase, signup 等
    event_value = Column(Float, nullable=True)  # 数值型指标
    event_data = Column(Text, nullable=True)  # JSON 附加数据
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_event_flag_type', 'flag_key', 'event_type'),
    )


